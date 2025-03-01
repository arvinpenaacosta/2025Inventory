// Working Deno QR Code Generator (No Terminal Output)
// Uses the QR code library from npm via esm.sh

import QRCode from "https://esm.sh/qrcode@1.5.3";
import { parse } from "https://deno.land/std@0.224.0/flags/mod.ts";
import { join } from "https://deno.land/std@0.224.0/path/mod.ts";

// Get system's temporary folder
const tempDir = Deno.env.get("TMP") || Deno.env.get("TEMP") || "/tmp";
const tempFilePath = join(tempDir, "qrcode2.png");

// Parse command line arguments
const args = parse(Deno.args, {
  string: ["output"],
  default: {
    output: tempFilePath, // Save to temp folder
  },
});

/**
 * Generates a QR code from the provided text and saves it as an image.
 * 
 * @param text - The text or JSON string to encode in the QR code.
 * @param outputFile - The file name for saving the QR code.
 */
async function generateQRCode(text: string, outputFile: string) {
  try {
    await QRCode.toFile(outputFile, text, {
      errorCorrectionLevel: "H",
      margin: 1,
      scale: 8,
      color: {
        dark: "#000000",
        light: "#ffffff",
      },
    });

    console.log(`QR code saved to: ${outputFile}`);
  } catch (error) {
    console.error("Error generating QR code:", error);
  }
}

// Example JSON contact information
const jsonData = JSON.stringify({
  name: "Arvin",
  age: 25,
  city: "New York",
  email: "arvin@example.com",
  phone: "+1-234-567-8901",
  skills: ["JavaScript", "Deno", "TypeScript"],
  experience: {
    company: "Tech Corp",
    position: "Software Engineer",
    years: 3,
  },
});

// Call the function with JSON data
await generateQRCode(jsonData, args.output);
