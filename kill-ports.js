const { execSync } = require('child_process');

const PORTS = [4000, 4001, 5000];
const isWindows = process.platform === 'win32';

console.log('👮‍♀️ Port cleanup utility');
console.log('===========================');

PORTS.forEach(port => {
  try {
    console.log(`Checking port ${port}...`);

    if (isWindows) {
      // For Windows, find PID using port and kill it
      const findCommand = `netstat -ano | findstr :${port}`;

      try {
        const output = execSync(findCommand, { encoding: 'utf8' });
        if (output) {
          // Extract PID from the last column
          const lines = output.split('\n').filter(line => line.includes(`LISTENING`));

          if (lines.length > 0) {
            lines.forEach(line => {
              const parts = line.trim().split(/\s+/);
              const pid = parts[parts.length - 1];

              if (pid && !isNaN(pid)) {
                console.log(`Found process ${pid} using port ${port}. Killing...`);
                try {
                  execSync(`taskkill /PID ${pid} /F`);
                  console.log(`✅ Successfully terminated process ${pid}`);
                } catch (err) {
                  console.error(`⚠️ Error terminating process: ${err.message}`);
                }
              }
            });
          } else {
            console.log(`No process found using port ${port}`);
          }
        } else {
          console.log(`No process found using port ${port}`);
        }
      } catch (error) {
        // If findstr doesn't find anything, it returns an error code
        console.log(`No process found using port ${port}`);
      }
    } else {
      // For Unix-like systems (MacOS/Linux)
      try {
        const output = execSync(`lsof -i :${port} -t`, { encoding: 'utf8' });
        if (output.trim()) {
          const pids = output.trim().split('\n');
          pids.forEach(pid => {
            console.log(`Found process ${pid} using port ${port}. Killing...`);
            try {
              execSync(`kill -9 ${pid}`);
              console.log(`✅ Successfully terminated process ${pid}`);
            } catch (err) {
              console.error(`⚠️ Error terminating process: ${err.message}`);
            }
          });
        } else {
          console.log(`No process found using port ${port}`);
        }
      } catch (error) {
        console.log(`No process found using port ${port}`);
      }
    }
  } catch (error) {
    console.error(`⚠️ Error checking port ${port}: ${error.message}`);
  }
});

console.log('===========================');
console.log('✅ Port cleanup completed');