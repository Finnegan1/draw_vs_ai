import psutil
import subprocess
import time

# Start the Flask server
flask_process = subprocess.Popen(['python', 'main.py'])

# Allow the server to start
time.sleep(5)

try:
    # Monitor resource usage
    while True:
        # Get the process ID of the Flask server
        flask_pid = flask_process.pid

        # Fetch process details using psutil
        process = psutil.Process(flask_pid)
        memory_info = process.memory_info()
        cpu_usage = process.cpu_percent(interval=1.0)

        # Print resource usage
        print(f"Memory Usage: {memory_info.rss / (1024 * 1024):.2f} MB")
        print(f"CPU Usage: {cpu_usage:.2f} %")

        # Wait for 5 seconds before checking again
        time.sleep(1)

except KeyboardInterrupt:
    # Terminate the Flask server on interrupt
    flask_process.terminate()
    flask_process.wait()

    print("Flask server terminated.")
