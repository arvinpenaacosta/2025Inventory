const username = prompt("Enter username:");
const password = prompt("Enter password:");

if (!username || !password) {
  console.error("Username and password are required!");
  Deno.exit(1);
}

// Run the Python script
const process = Deno.run({
  cmd: ["python", "authentication2.py", username, password],
  stdout: "piped",
  stderr: "piped",
});

// Capture output and error
const output = await process.output();
const error = await process.stderrOutput();

// Handle error output first
if (error.length > 0) {
  console.error(new TextDecoder().decode(error));
  Deno.exit(1); // Exit if there was an error
}

// Decode the output from the Python script
const outputStr = new TextDecoder().decode(output).trim();

// Check if the output is a success or failure message
if (outputStr === "True") {
  console.log("Login successful!");
} else {
  console.log("Login failed. Please check your username or password.");
}

// Close the process
process.close();
