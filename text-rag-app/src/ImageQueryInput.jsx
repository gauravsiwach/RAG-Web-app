import React, { useState, useRef } from 'react';
import { analyzeImage } from './services/azureVisionService';

const ImageQueryInput = ({ onImageText, disabled }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const fileInputRef = useRef(null);

  const handleImageSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select a valid image file');
      return;
    }

    // Validate file size (max 20MB)
    if (file.size > 20 * 1024 * 1024) {
      alert('Image size must be less than 20MB');
      return;
    }

    setIsProcessing(true);

    try {
      console.log("🖼️ Processing image for query:", file.name);
      
      // Create image preview URL
      const imageUrl = URL.createObjectURL(file);
      
      // Analyze the image
      const result = await analyzeImage(file);
      
      console.log("✅ Image analysis result:", result);
      
      // Extract text for query (silently, not shown to user)
      let queryText = '';
      
      if (result.text) {
        queryText = result.text;
      } else if (result.caption && result.caption !== 'No caption available') {
        queryText = result.caption;
      } else {
        queryText = 'Analyze this image';
      }
      
      // Send the extracted text as query with image preview
      if (onImageText) {
        onImageText(queryText.trim(), true, imageUrl); // true = auto-send, imageUrl = for display
      }

    } catch (err) {
      console.error('❌ Image processing error:', err);
      
      if (err.message.includes('credentials not configured')) {
        alert('Azure Vision Service not configured. Please check your .env file.');
      } else if (err.message.includes('401')) {
        alert('Invalid Azure Vision credentials. Please check your API key.');
      } else {
        alert(`Image processing failed: ${err.message}`);
      }
    } finally {
      setIsProcessing(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleButtonClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageSelect}
        style={{ display: 'none' }}
      />
      <button
        onClick={handleButtonClick}
        disabled={disabled || isProcessing}
        style={{
          padding: '10px 15px',
          backgroundColor: isProcessing ? '#94a3b8' : '#8b5cf6',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: disabled || isProcessing ? 'not-allowed' : 'pointer',
          fontSize: '18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minWidth: '50px',
          opacity: disabled || isProcessing ? 0.5 : 1,
          transition: 'all 0.2s',
        }}
        title={isProcessing ? "Processing image..." : "Upload image as query"}
      >
        {isProcessing ? '🔄' : '🖼️'}
      </button>
    </>
  );
};

export default ImageQueryInput;
