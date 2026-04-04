import * as SpeechSDK from 'microsoft-cognitiveservices-speech-sdk';

const SPEECH_KEY = import.meta.env.VITE_AZURE_SPEECH_KEY;
const SPEECH_REGION = import.meta.env.VITE_AZURE_SPEECH_REGION;

/**
 * Recognizes speech from microphone using Azure Speech Service
 * @returns {Promise<string>} - Transcribed text
 */
export const recognizeSpeechFromMicrophone = (userLanguage = "en-US") => {
  console.log("inside recognizeSpeechFromMicrophone Service.....");
  
  return new Promise((resolve, reject) => {
    if (!SPEECH_KEY || !SPEECH_REGION) {
      reject(new Error('Azure Speech credentials not configured. Please set VITE_AZURE_SPEECH_KEY and VITE_AZURE_SPEECH_REGION in .env file.'));
      return;
    }

    const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(SPEECH_KEY, SPEECH_REGION);
    speechConfig.speechRecognitionLanguage = userLanguage;

    const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
    const recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

    console.log('🎤 Listening... Speak into your microphone.');

    recognizer.recognizeOnceAsync(
      (result) => {
        if (result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
          console.log(`✅ Recognized: ${result.text}`);
          resolve(result.text);
        } else if (result.reason === SpeechSDK.ResultReason.NoMatch) {
          reject(new Error('No speech could be recognized. Please try again.'));
        } else if (result.reason === SpeechSDK.ResultReason.Canceled) {
          const cancellation = SpeechSDK.CancellationDetails.fromResult(result);
          reject(new Error(`Speech recognition canceled: ${cancellation.reason}. ${cancellation.errorDetails}`));
        }
        recognizer.close();
      },
      (error) => {
        console.error('❌ Speech recognition error:', error);
        reject(error);
        recognizer.close();
      }
    );
  });
};

/**
 * Continuous speech recognition (for advanced use cases)
 * @param {Function} onRecognized - Callback when speech is recognized
 * @param {Function} onError - Callback when error occurs
 * @returns {SpeechRecognizer|null} - Recognizer instance or null
 */
export const recognizeSpeechContinuous = (onRecognized, onError, userLanguage = "en-US") => {
  if (!SPEECH_KEY || !SPEECH_REGION) {
    onError(new Error('Azure Speech credentials not configured.'));
    return null;
  }

  const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(SPEECH_KEY, SPEECH_REGION);
  speechConfig.speechRecognitionLanguage = userLanguage;

  const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
  const recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

  recognizer.recognized = (s, e) => {
    if (e.result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
      console.log(`✅ Recognized: ${e.result.text}`);
      onRecognized(e.result.text);
    }
  };

  recognizer.canceled = (s, e) => {
    onError(new Error(`Recognition canceled: ${e.reason}`));
    recognizer.stopContinuousRecognitionAsync();
  };

  recognizer.startContinuousRecognitionAsync();

  return recognizer;
};
