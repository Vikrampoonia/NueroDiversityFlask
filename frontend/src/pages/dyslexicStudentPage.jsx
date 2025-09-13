import React, { useState, useRef,useEffect } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import "../styles/dyslexia.css";

// --- Configuration ---
const BACKEND_URL = "http://127.0.0.1:5000"; // Our single API Gateway

// --- SVG Icon Components (Self-contained to avoid external dependencies) ---
const CloudUploadIcon = (props) => (
    <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 512 512" {...props}>
        <path d="M398.1 214.5c-11.2-51.1-58.3-86.5-110.4-86.5-43.5 0-83.3 24-104.2 60.1-21.2-10.7-45.8-16.6-71.5-16.6-69.5 0-126 56.5-126 126 0 28.5 9.5 54.8 25.5 76.3L112 416h288l14.5-43.7c16-21.5 25.5-47.8 25.5-76.3 0-69.5-56.5-126-126-126-25.7 0-50.3 5.9-71.5 16.6-20.9-36.1-60.7-60.1-104.2-60.1-52.1 0-99.2 35.4-110.4 86.5C83.9 221.1 32 263.1 32 314c0 60.8 49.2 110 110 110h228c60.8 0 110-49.2 110-110 0-50.9-51.9-92.9-117.9-99.5zM352 328h-64v64h-64v-64h-64l96-96 96 96z"></path>
    </svg>
);

const CheckCircleIcon = (props) => (
    <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 512 512" {...props}>
        <path d="M504 256c0 136.967-111.033 248-248 248S8 392.967 8 256 119.033 8 256 8s248 111.033 248 248zM227.314 387.314l184-184c6.248-6.248 6.248-16.379 0-22.627l-22.627-22.627c-6.248-6.249-16.379-6.249-22.628 0L216 308.118l-70.059-70.059c-6.248-6.248-16.379-6.248-22.628 0l-22.627 22.627c-6.248 6.248-6.248 16.379 0 22.627l104 104c6.249 6.249 16.379 6.249 22.628 0z"></path>
    </svg>
);

const HourglassHalfIcon = (props) => (
    <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 384 512" {...props}>
        <path d="M360 0H24A24.002 24.002 0 000 24v56a24.002 24.002 0 0024 24h13.2l126.4 158-126.4 158H24a24.002 24.002 0 00-24 24v56a24.002 24.002 0 0024 24h336a24.002 24.002 0 0024-24v-56a24.002 24.002 0 00-24-24h-13.2L220.4 256l126.4-158H360a24.002 24.002 0 0024-24V24A24.002 24.002 0 00360 0zm0 464H24v-32h336zm-179.6-208L54.8 128H329.2z"></path>
    </svg>
);

const ExclamationCircleIcon = (props) => (
    <svg stroke="currentColor" fill="currentColor" strokeWidth="0" viewBox="0 0 512 512" {...props}>
        <path d="M504 256c0 136.997-111.003 248-248 248S8 392.997 8 256C8 119.003 119.003 8 256 8s248 111.003 248 248zm-248 50c-25.405 0-46 20.595-46 46s20.595 46 46 46 46-20.595 46-46-20.595-46-46-46zm-43.673-165.346l7.418 136c.347 6.364 5.609 11.346 11.982 11.346h48.546c6.373 0 11.635-4.982 11.982-11.346l7.418-136c.375-6.874-5.098-12.654-11.982-12.654h-63.383c-6.884 0-12.356 5.78-11.981 12.654z"></path>
    </svg>
);


export default function DyslexicToolPage({ navigate }) {
    const [file, setFile] = useState(null);
    const [tasks, setTasks] = useState({});
    const [error, setError] = useState('');
    const [summary, setSummary] = useState('');
    const [isSummarizing, setIsSummarizing] = useState(false);
    const intervalRef = useRef(null);

    // This effect polls for the status of any active asynchronous tasks.
    useEffect(() => {
        const activeTasks = Object.values(tasks).filter(t => t.state === 'PENDING' || t.state === 'STARTED');
        
        if (activeTasks.length > 0) {
            intervalRef.current = setInterval(async () => {
                for (const task of activeTasks) {
                    if (task.state !== 'SUCCESS' && task.state !== 'FAILURE') {
                        try {
                            const res = await axios.get(`${BACKEND_URL}/api/task-status/${task.task_id}`);
                            setTasks(prev => ({ ...prev, [task.task_id]: { ...prev[task.task_id], ...res.data } }));
                        } catch (e) {
                            console.error("Polling error", e);
                        }
                    }
                }
            }, 3000); // Poll every 3 seconds
        } else {
            clearInterval(intervalRef.current);
        }

        // Cleanup interval on component unmount
        return () => clearInterval(intervalRef.current);
    }, [tasks]);

    // Handles file selection from both drag-and-drop and file input.
    const handleFileSelect = (selectedFile) => {
        if (selectedFile && selectedFile.type === "application/pdf") {
            setFile(selectedFile);
            setSummary(''); // Clear previous summary
            setError('');
            setTasks({}); // Clear previous tasks
        } else {
            setError("Please select a valid PDF file.");
        }
    };
    
    // Starts an asynchronous task (e.g., audio conversion, PDF generation).
    const startAsyncTask = async (endpoint, operationName) => {
        if (!file) {
            setError("Please select a file first.");
            return;
        }
        setError('');
        setSummary('');
        const formData = new FormData();
        formData.append("file", file);
        
        try {
            const res = await axios.post(`${BACKEND_URL}/api/${endpoint}`, formData);
            //console.log("Task Started Res:", JSON.stringify(res, null, 2));
            const { task_id } = res.data;
            setTasks(prev => ({ ...prev, [task_id]: { task_id, state: 'PENDING', operation: operationName } }));
        } catch (err) {
            setError(`Error starting ${operationName} task.`);
            console.error(err);
        }
    };

    // Handles the synchronous summarization task.
    const handleSummarize = async () => {
        if (!file) {
            setError("Please select a file first.");
            return;
        }
        setIsSummarizing(true);
        setError('');
        setTasks({}); // Clear async tasks
        const formData = new FormData();
        formData.append("file", file);

        try {
            // Step 1: Extract text from the PDF.
            const textResponse = await axios.post(`${BACKEND_URL}/api/process-text-from-pdf`, formData);
           // console.log("Extracted Text:", JSON.stringify(textResponse.data.result));
            // Step 2: Send the extracted text to the summarizer.
            const summaryResponse = await axios.post(`${BACKEND_URL}/api/process-text`, {
                operation: 'summarize',
                text: textResponse.data.result
            });
           // console.log("Summary Response:", JSON.stringify(summaryResponse));
            setSummary(summaryResponse.data.result);
        } catch (err) {
            setError("Failed to generate summary.");
            console.error(err);
        } finally {
            setIsSummarizing(false);
        }
    };
    
    // Utility to get the base filename from a full path.
    const getFileName = (path) => {
        if (!path) return '';
        return path.split('\\').pop().split('/').pop();
    }

    // Renders the result of a completed asynchronous task.
    const renderTaskResult = (task) => {
        if (task.state === 'SUCCESS') {
            const filePath = task.result;
            const fileName = getFileName(filePath);
            const downloadUrl = `${BACKEND_URL}/api/download/${fileName}`;
            const isAudio = filePath.endsWith('.mp3');

            return isAudio ? (
                <audio controls src={downloadUrl} className="w-full max-w-xs">Your browser does not support the audio element.</audio>
            ) : (
                <a href={downloadUrl} download className="font-semibold text-indigo-600 hover:underline">Download File</a>
            );
        }
        return null;
    };

    return (
        <div className="min-h-screen w-full flex flex-col items-center bg-gray-100 p-4 font-sans">
             {/* Back Button */}
             <div className="w-full max-w-3xl">
                <button onClick={() => navigate('landing')} className="absolute top-4 left-4 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors">
                    &larr; Back to Home
                </button>
             </div>

            <div className="w-full max-w-3xl bg-white rounded-xl shadow-lg p-8 mt-16">
                 <h2 className="text-3xl font-bold text-gray-800 mb-2 text-center">Dyslexia Accessibility Tool</h2>
                <p className="text-gray-600 mb-6 text-center">Upload a PDF to convert it into more accessible formats.</p>

                {/* File Upload Area */}
                <div
                    className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors duration-300 ${'border-gray-300'}`}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                        e.preventDefault();
                        if (e.dataTransfer.files.length > 0) {
                           handleFileSelect(e.dataTransfer.files[0]);
                        }
                    }}
                >
                    <input id="dyslexicFileInput" type="file" accept="application/pdf" onChange={(e) => handleFileSelect(e.target.files[0])} className="hidden" />
                    <label htmlFor="dyslexicFileInput" className="cursor-pointer text-purple-600 font-semibold">
                        <CloudUploadIcon className="mx-auto text-4xl text-gray-400 mb-2" />
                        {file ? `Selected: ${file.name}` : 'Click to select a PDF or drag and drop here'}
                    </label>
                </div>
                 {error && <p className="mt-4 text-red-500 text-center">{error}</p>}
                 
                {/* Action Buttons */}
                <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                     <button onClick={handleSummarize} disabled={!file || isSummarizing} className="w-full py-3 bg-purple-600 text-white font-bold rounded-lg shadow-md hover:bg-purple-700 disabled:bg-gray-400 transition-all">
                         {isSummarizing ? 'Summarizing...' : 'Summarize Text'}
                     </button>
                     <button onClick={() => startAsyncTask('pdf-to-speech', 'Text-to-Speech')} disabled={!file} className="w-full py-3 bg-purple-600 text-white font-bold rounded-lg shadow-md hover:bg-purple-700 disabled:bg-gray-400 transition-all">Convert to Audio</button>
                     <button onClick={() => startAsyncTask('generate-dyslexic-pdf', 'Dyslexia-Friendly PDF')} disabled={!file} className="w-full py-3 bg-purple-600 text-white font-bold rounded-lg shadow-md hover:bg-purple-700 disabled:bg-gray-400 transition-all">Create Dyslexic PDF</button>
                </div>

                {/* Results Area */}
                <div className="mt-8 space-y-4">
                    {summary && !isSummarizing && (
                        <div className="bg-gray-50 p-4 rounded-lg animate-fade-in">
                            <h3 className="font-bold text-lg mb-2 text-gray-800">Summary:</h3>
                            <p className="text-gray-700 whitespace-pre-wrap">{summary}</p>
                        </div>
                    )}
                    {Object.values(tasks).map(task => (
                        <div key={task.task_id} className="bg-gray-50 p-4 rounded-lg flex flex-col sm:flex-row items-center justify-between animate-fade-in">
                            <div className="mb-2 sm:mb-0 text-center sm:text-left">
                                <p className="font-semibold text-gray-800">{task.operation}</p>
                                <p className="text-sm text-gray-500">Status: {task.state}</p>
                            </div>
                            <div className="flex items-center space-x-4">
                                {(task.state === 'PENDING' || task.state === 'STARTED') && <HourglassHalfIcon className="text-yellow-500 text-2xl animate-spin" />}
                                {task.state === 'SUCCESS' && <CheckCircleIcon className="text-green-500 text-2xl" />}
                                {task.state === 'FAILURE' && <ExclamationCircleIcon className="text-red-500 text-2xl" />}
                                {renderTaskResult(task)}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

// You would import this component in your App.js router
// export default DyslexicToolPage;
{/*import React, { useState, useRef } from "react";
import axios from "axios";
import { FaCloudUploadAlt } from "react-icons/fa";
import { motion } from "framer-motion";
import "../styles/dyslexia.css";

const backendUrl = "http://127.0.0.1:5000";

function PdfToSummariser() 
{
  const fileInputRef = useRef(null);
  const [fileName, setFileName] = useState("");
  //const [pdfFile, setPdfFile] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState("");
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");
  

   const handleDivClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFileName(e.target.files[0].name);
      setUploadedFileName(e.target.files[0].name);
    }
  };



  // ✅ Convert PDF: Receives a Blob and allows downloading
  const handlePdfConversion = async () => {
    if (!fileName) return;
    try {
      
      // Fetching Blob response
      setLoading(true);
      const response = await axios.post(`${backendUrl}/generate-pdf`, {}, {
        responseType: "blob", // Expecting binary data
      });
  
      // Ensure we receive a valid Blob
      if (!response.data || response.data.size === 0) {
        throw new Error("Received empty PDF file.");
      }
  
      // Convert Blob to downloadable URL
      const pdfBlob = new Blob([response.data], { type: "application/pdf" });
      const blobUrl = URL.createObjectURL(pdfBlob);
  
      setOutput(
        <a href={blobUrl} download="dyslexic_friendly.pdf" className="link">
          Click to download PDF
        </a>
      );
      setLoading(false)
  
    } catch (error) {
      console.error("Error converting to PDF:", error);
      alert("Failed to convert to PDF!");
    }
  };

  // ✅ Convert Audio: Receives a Blob and plays it
  const handleAudioConversion = async () => {
    if (!uploadedFileName) {
      alert("No file selected!");
      return;
    }
  
    try {
      setLoading(true);
      const response = await axios.get(`${backendUrl}/text_to_speech?file_name=${uploadedFileName}`, {
        responseType: "blob", // Ensure correct response format
      });
  
      if (!response.data || response.data.size === 0) {
        throw new Error("Received an empty audio file.");
      }
  
      // Convert Blob to URL for playback
      const audioBlob = new Blob([response.data], { type: "audio/mpeg" });
      const audioUrl = URL.createObjectURL(audioBlob);
  
      setOutput(
        <audio controls>
          <source src={audioUrl} type="audio/mpeg" />
          Your browser does not support the audio element.
        </audio>
      );
      setLoading(false);
    } catch (error) {
      console.error("Error converting to audio:", error);
      alert(`Error: ${error.message}`);
    }
  };

  const handleSummarization = async () => {
    try {
      setLoading(true);
      const response = await axios.post("http://localhost:5001/summarize");
      setSummary(response.data.summary);
      // console.log(summary)
      setOutput(<textarea className="output-textarea auto-expand" readOnly value={summary} />);
      setError("");
    } catch (err) {
      console.error("Summarization error:", err);
      setError("Error summarizing the text.");
    } finally {
      setLoading(false);
    }
  };



  

  return (
    <div className="container">
      <h2 className="title">PDF Summarizer</h2>
      <div className="upload-section">
        <label className="label">Upload PDF:</label>
        <div 
        className={`drop-area flex justify-center flex-col items-center`}
        onClick={handleDivClick}>
          <FaCloudUploadAlt size={50} className="upload-icon" />
          <p className="drop-text">
            Drag & Drop your PDF here or <span className="highlight">click to select</span>
          </p>
        </div>

        <input
          type="file"
          accept="application/pdf"
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={handleFileChange}
        />
       

        {fileName && <p className="selected-file">Selected File: {fileName}</p>}
      </div>
      <div className="button-group">
        <button onClick={handlePdfConversion} className="convert-btn">Convert to PDF</button>
        <button onClick={handleAudioConversion} className="convert-btn">Convert to Audio</button>
        <button onClick={handleSummarization} className="convert-btn">Summarize</button>
      </div>
      {loading ? (
          <div className="flex justify-center items-center gap-2 h-16">
          {[1, 2, 3, 4].map((i) => (
            <motion.div
              key={i}
              className="w-4 h-12 bg-blue-500 rounded"
              animate={{ y: [-10, 10, -10] }}
              transition={{
                duration: 0.6,
                repeat: Infinity,
                repeatType: "reverse",
                delay: i * 0.1,
              }}
            />
          ))}
        </div>
        ) : (
          output && (
            <div className="output-section">
              <h3 className="output-title">Output:</h3>
              <div className="text-blue-700 underline">{output}</div>
            </div>
          )
        )}
    </div>
  );
}

export default PdfToSummariser;
*/}