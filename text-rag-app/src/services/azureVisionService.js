import ImageAnalysisClient from '@azure-rest/ai-vision-image-analysis';
import { AzureKeyCredential } from '@azure/core-auth';

const VISION_KEY = import.meta.env.VITE_AZURE_VISION_KEY;
const VISION_ENDPOINT = import.meta.env.VITE_AZURE_VISION_ENDPOINT;

/**
 * Analyzes an image using Azure Computer Vision REST API
 * @param {File} imageFile - The image file to analyze
 * @returns {Promise<Object>} - Analysis results
 */
export const analyzeImage = async (imageFile) => {
  console.log("🖼️ Starting image analysis...");
  
  if (!VISION_KEY || !VISION_ENDPOINT) {
    throw new Error('Azure Vision credentials not configured. Please set VITE_AZURE_VISION_KEY and VITE_AZURE_VISION_ENDPOINT in .env file.');
  }

  try {
    // Create the client
    const credential = new AzureKeyCredential(VISION_KEY);
    const client = new ImageAnalysisClient(VISION_ENDPOINT, credential);

    // Convert File to ArrayBuffer
    const imageBuffer = await imageFile.arrayBuffer();
    const imageData = new Uint8Array(imageBuffer);

    console.log("📤 Sending image to Azure Vision API...");

    // Analyze the image with all features
    const result = await client.path("/imageanalysis:analyze").post({
      body: imageData,
      queryParameters: {
        features: ["Caption", "DenseCaptions", "Objects", "Tags", "Read"],
      },
      contentType: "application/octet-stream",
    });

    console.log("✅ Image analysis complete:", result.body);

    // Extract and structure the results
    const analysisResult = {
      text: extractTextFromResult(result.body),
      caption: result.body.descriptionResult?.captions?.[0]?.text || 'No caption available',
      confidence: result.body.descriptionResult?.captions?.[0]?.confidence || 0,
      objects: result.body.objectsResult?.values?.map(obj => ({
        name: obj.tags?.[0]?.name || obj.object || 'Unknown',
        confidence: obj.confidence,
      })) || [],
      tags: result.body.tagsResult?.values?.map(tag => ({
        name: tag.name,
        confidence: tag.confidence,
      })) || [],
      metadata: {
        width: result.body.metadata?.width,
        height: result.body.metadata?.height,
      }
    };

    return analysisResult;

  } catch (error) {
    console.error('❌ Image analysis error:', error);
    throw error;
  }
};

/**
 * Extract text from Azure Vision result
 * @param {Object} result - Azure Vision API result
 * @returns {string} - Extracted text
 */
const extractTextFromResult = (result) => {
  if (result.readResult?.blocks) {
    return result.readResult.blocks
      .flatMap(block => block.lines || [])
      .map(line => line.text)
      .join('\n');
  }
  return '';
};

/**
 * Extract only text from image (OCR)
 * @param {File} imageFile - The image file
 * @returns {Promise<string>} - Extracted text
 */
export const extractTextFromImage = async (imageFile) => {
  const result = await analyzeImage(imageFile);
  return result.text;
};

/**
 * Get image description/caption
 * @param {File} imageFile - The image file
 * @returns {Promise<Object>} - Caption and confidence
 */
export const getImageCaption = async (imageFile) => {
  const result = await analyzeImage(imageFile);
  return {
    caption: result.caption,
    confidence: result.confidence
  };
};

/**
 * Comprehensive image analysis (text + caption + objects)
 * @param {File} imageFile - The image file
 * @returns {Promise<Object>} - Complete analysis
 */
export const analyzeImageComprehensive = async (imageFile) => {
  return await analyzeImage(imageFile);
};
