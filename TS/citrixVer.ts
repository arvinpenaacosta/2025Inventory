const runCommand = async (cmd: string[]) => {
  const process = new Deno.Command("cmd", {
    args: ["/c", ...cmd],  // The "/c" flag tells cmd to execute the command and then terminate
    stdout: "piped",
    stderr: "piped",
  }).spawn();

  const { stdout, stderr } = await process.output();

  if (stderr.length > 0) {
    console.error(new TextDecoder().decode(stderr));
    return null;
  }
  return new TextDecoder().decode(stdout).trim();
};

async function searchRegistryWithGUID(hive: string, path: string, searchPattern: string) {
  // Use the custom runCommand function to query the registry
  const outputString = await runCommand(["reg", "query", `${hive}\\${path}`, "/s"]);
  if (outputString === null) {
    return;
  }

  const lines = outputString.split("\n");

  let foundMatch = false;
  const searchPatternLower = searchPattern.toLowerCase();
  let displayName = '';
  let displayVersion = '';

  for (const line of lines) {
    if (line.toLowerCase().includes("displayname") && line.toLowerCase().includes(searchPatternLower)) {
      displayName = line.trim().split('REG_SZ')[1]?.trim();  // Get the value after REG_SZ
    }

    if (line.toLowerCase().includes("displayversion") && displayName !== '') {
      displayVersion = line.trim().split('REG_SZ')[1]?.trim();  // Get the value after REG_SZ
    }

    // If both DisplayName and DisplayVersion have been found, print the cleaned values
    if (displayName && displayVersion) {
      console.log(`Found Match:`);
      console.log(`${displayName}`);
      console.log(`${displayVersion}`);
      foundMatch = true;
      break;
    }
  }

  if (!foundMatch) {
    console.log(`No matches found for pattern: "${searchPattern}"`);
  }
}

// Example usage: search for a GUID or software name in the registry
const hive = "HKLM";
const path = "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall";
const searchPattern = "Citrix Workspace";

await searchRegistryWithGUID(hive, path, searchPattern);
