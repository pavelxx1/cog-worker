import time
import subprocess

import runpod
import requests
from requests.adapters import HTTPAdapter, Retry

LOCAL_URL = "http://127.0.0.1:5000"

cog_session = requests.Session()
retries = Retry(total=10, backoff_factor=0.1, status_forcelist=[502, 503, 504])
cog_session.mount('http://', HTTPAdapter(max_retries=retries))


# ----------------------------- Start API Service ---------------------------- #
# Call "python -m cog.server.http" in a subprocess to start the API service.
subprocess.Popen(["python", "-m", "cog.server.http"])


# ---------------------------------------------------------------------------- #
#                              Automatic Functions                             #
# ---------------------------------------------------------------------------- #
def wait_for_service(url):
    '''
    Check if the service is ready to receive requests.
    '''
    while True:
        try:
            health = requests.get(url, timeout=120)
            status = health.json()["status"]

            if status == "READY":
                time.sleep(1)
                return

        except requests.exceptions.RequestException:
            print("Service not ready yet. Retrying...")
        except Exception as err:
            print("Error: ", err)

        time.sleep(0.2)


def run_inference(inference_request):
    '''
    Run inference on a request.
    '''
    response = cog_session.post(url=f'{LOCAL_URL}/predictions',
                                json=inference_request, timeout=600)
    return response.json()


# ---------------------------------------------------------------------------- #
#                                RunPod Handler                                #
# ---------------------------------------------------------------------------- #
def handler(event):
    '''
    This is the handler function that will be called by the serverless.
    '''

    # json_response = run_inference({"input": event["input"]})

    # # Check if json_response is a list or dictionary and handle accordingly
    # if isinstance(json_response, list):
    #     # Handle the case where json_response is a list
    #     # Assuming the output we need is in the first element
    #     if json_response and "output" in json_response[0]:
    #         return json_response[0]["output"]
    #     else:
    #         raise ValueError("Invalid response format: 'output' key not found in list element")
    # elif isinstance(json_response, dict):
    #     # Handle the case where json_response is a dictionary
    #     if "output" in json_response:
    #         return json_response["output"]
    #     else:
    #         raise ValueError("Invalid response format: 'output' key not found in dictionary")
    # else:
    #     # Handle unexpected cases
    #     raise TypeError("Unexpected type for json_response variable")

    try:
        json_response = run_inference({"input": event["input"]})
    
        # Check if json_response is a list or dictionary and handle accordingly
        if isinstance(json_response, list):
            # Handle the case where json_response is a list
            # Assuming the output we need is in the first element
            return json_response[0]["output"]
        elif isinstance(json_response, dict):
            # Handle the case where json_response is a dictionary
            return json_response["output"]
        else:
            # Handle unexpected cases
            print(' *** Type json_response is:',type(json_response))
            raise TypeError("Unexpected type for json_response variable")
    
    except Exception as e:
        print(f"An error occurred: {e}")



if __name__ == "__main__":
    wait_for_service(url=f'{LOCAL_URL}/health-check')

    print("Cog API Service is ready. Starting RunPod serverless handler...")

    runpod.serverless.start({"handler": handler})
