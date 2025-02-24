const textEncoder = new TextEncoder();
const textDecoder = new TextDecoder();

// Print prompt without a newline (stays on the same line)
await Deno.stdout.write(textEncoder.encode("Select a floor: "));

const inputBuffer = new Uint8Array(1024);
const bytesRead = await Deno.stdin.read(inputBuffer);

if (bytesRead !== null) {
    const selectedFloor = textDecoder.decode(inputBuffer.subarray(0, bytesRead)).trim();
    console.log(`You selected: ${selectedFloor}`);
}
