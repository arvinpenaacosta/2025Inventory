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

// Generate QR Code
await generateQRCode(jsonData, args.output);

// Open Image in Browser
const imagePath = `file:///${args.output}`;

const browserCommands: Record<string, string[]> = {
  windows: ["cmd", "/c", "start", "chrome", imagePath], // Change to "msedge" or "firefox" if needed
  darwin: ["open", "-a", "Google Chrome", imagePath], // macOS
  linux: ["google-chrome", imagePath], // Linux (Change to "firefox" if needed)
};

const osType = Deno.build.os;
if (browserCommands[osType]) {
  await new Deno.Command(browserCommands[osType][0], {
    args: browserCommands[osType].slice(1),
  }).output();
} else {
  console.error("Unsupported OS. Please open the file manually:", imagePath);
}
