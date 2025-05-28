// src/App.js
import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import "./App.css"; // optional

function App() {
  const [quotes, setQuotes] = useState([
    "Security through simplicity.",
    "Hacking is not a crime.",
    "Knowledge is power."
  ]);
  const [quoteIndex, setQuoteIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setQuoteIndex((prev) => (prev + 1) % quotes.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [quotes.length]);

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center px-4" style={{ minHeight: "100vh", backgroundColor: "#000", color: "#fff", textAlign: "center" }}>
      <motion.h1
        className="text-4xl font-bold mb-8"
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        BRUTSEC Clone
      </motion.h1>

      <motion.p
        key={quoteIndex}
        className="text-xl text-gray-400 mb-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        {quotes[quoteIndex]}
      </motion.p>

      <div style={{ background: '#111', padding: '1rem', borderRadius: '1rem', maxWidth: '600px', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>About</h2>
        <p style={{ color: '#ccc' }}>
          This is a simple static site built for a college project inspired by Brutsec.com.
          It showcases minimalistic design, dark aesthetics, and a security-focused message.
        </p>
      </div>

      <footer style={{ color: '#666', fontSize: '0.875rem' }}>
        © {new Date().getFullYear()} BRUTSEC Clone. Built for educational purposes.
      </footer>
    </div>
  );
}

export default App;
