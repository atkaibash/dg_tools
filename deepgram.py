#!/usr/bin/env python3

import argparse
import base64
import getpass
import http.client
import json
import os

def parse_args():
    docsURL = "https://developers.deepgram.com/api-reference/speech-recognition-api#operation/transcribeAudio/properties/"
    p = argparse.ArgumentParser(
        description="""
        A wrapper for the Deepgram transcription API. More info available at: 
        https://developers.deepgram.com/api-reference/speech-recognition-api#operation/transcribeAudio/ 
        """,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument(
        "--user",
        "-u",
        dest="user",
        default=False,
        action="store",
        help="This should be the username for https://missioncontrol.deepgram.com/",
    )
    p.add_argument(
        "--password",
        "-p",
        dest="password",
        default=False,
        action="store",
        help="Not required, you will be prompted for a password.",
    )
    p.add_argument(
        "--store-credentials",
        "-sc",
        dest="creds",
        action="store_true",
        help="Store credentials into the environment variable DG_AUTH.",
    )
    p.add_argument(
        "--file",
        "-f",
        dest="input_file",
        default=False,
        action="store",
        help="Specify a file to transcribe, or a local transcript to parse if --local is set.",
    )
    p.add_argument(
        "--dir",
        "-d",
        dest="input_dir",
        default=False,
        action="store",
        help="Transcribe the files in the given directory. The directory should only contain audio files.",
    )
    p.add_argument(
        "--output",
        "-o",
        dest="output_folder",
        default=False,
        action="store",
        help="Save transcription output to the specified folder. Do not save transcripts into audio folder.",
    )
    p.add_argument(
        "--local",
        "-l",
        dest="local",
        default=False,
        action="store_true",
        help="Read from local transcripts.",
    )
    p.add_argument(
        "--url",
        dest="url",
        default=False,
        action="store",
        help="Transcribe the the file at the given URL",
    )
    p.add_argument(
        "--model",
        dest="model",
        default=False,
        action="store",
        help=docsURL + "model",
    )
    p.add_argument(
        "--language",
        dest="language",
        action="store",
        choices=['en-GB', 'en-IN', 'en-NZ', 'en-US',
            'es', 'fr', 'hi', 'ko', 'pt', 'pt-BR',
            'ru', 'tr', 'null'],
        default='en-US',
        help=docsURL + "language",
    )
    p.add_argument(
        "--punctuate",
        dest="punctuate",
        default=False,
        action="store_true",
        help="Add punctuation and capitalization to the transcript? \n{}punctuate".format(docsURL),
    )
    p.add_argument(
        "--redact",
        dest="redact",
        action="store",
        choices=['pci', 'numbers', 'ssn', 'true', 'null'],
        default=False,
        help="Indicates whether to redact sensitive information, replacing redacted content with asterisks.\
        \n{}redact".format(docsURL),
    )
    p.add_argument(
        "--verbose",
        "-v",
        dest="verbose",
        default=False,
        action="store_true",
        help="Return all query data instead of just transcript.",
    )
    p.add_argument(
        "--parameters",
        "-prms",
        dest="params",
        action="store",
        default=False,
        help="Insert any additional parameters in one big string",
    )
    p.add_argument(
        "--search",
        dest="search",
        action="store",
        default=False,
        help="Search the audio file for the given words. \n{}search".format(docsURL),
    )
    p.add_argument(
        "--search-threshold",
        dest="search-threshold",
        action="store",
        default=False,
        help="Sets a threshold to only return searches results above that threshold. Values between [0-1].",
    )
    p.add_argument(
        "--fqdn",
        dest="fqdn",
        action="store",
        default="brain.deepgram.com",
        help="Set the FQDN for your queries.",
    )
    args = p.parse_args()

    return args


def parseCredentials(args):
    usr = ""
    passwd = ""

    if not args.creds and "DG_AUTH" in os.environ:
        return os.environ["DG_AUTH"]

    if args.user:
        usr = args.user
    else:
        usr = input("Username:")

    if not args.password:
        passwd = str(getpass.getpass("Password:"))
    else:
        passwd = str(args.password)

    rawAuthBytes = str(str(usr) + ":" + str(passwd)).encode("utf-8")

    encodedAuth = base64.b64encode(rawAuthBytes).decode("utf-8")

    if args.creds:
        shell = os.environ['SHELL']
        if  "zsh" in shell:
            print ("Saving encoded credentials to DG_AUTH to your zsh profile.")
            os.system("echo 'export DG_AUTH={}' >> ~/.zshrc".format(encodedAuth))
        elif "bash" in shell: 
            print ("Saving encoded credentials to DG_AUTH to your bash profile.")
            os.system("echo 'export DG_AUTH={}' >> ~/.bash_profile".format(encodedAuth))
        else:
            print("I'm not sure what your shell is. You can add DG_AUTH={} to your\
            environment variables".format(encodedAuth))
        os.system('export DG_AUTH={}'.format(encodedAuth))

    return encodedAuth


def parseQuery(args):
    apiParams = ""
    apiChar = "?"
    if args.model:
        apiParams += str(apiChar + "model=" + args.model)
        apiChar ="&"
    if args.language:
        apiParams += str(apiChar + "language=" + str(args.language))
        apiChar ="&"
    if args.punctuate: 
        apiParams += str(apiChar + "punctuate=true")
        apiChar ="&"
    if args.redact: 
        apiParams += str(apiChar + "redact=" + str(args.redact))
        apiChar ="&"
    if args.search:
        apiParams += str(apiChar + "search=" + str(args.search))
        apiChar ="&"
    if args.params:
        apiParams += str(apiChar + args.params)
    return apiParams


def getTranscipt(args, fileFromDir=False):
    conn = http.client.HTTPSConnection(str(args.fqdn))
    queryHeaders ={}
    if args.input_file:
        queryHeaders['content-type'] = 'binary/message-pack'
        payload = open(args.input_file, "rb")
    elif fileFromDir:
        queryHeaders['content-type'] = 'binary/message-pack'
        payload = open(fileFromDir, "rb")
    elif args.url:
        queryHeaders['content-type'] = "application/json"
        payload = "{\"url\":\"" + str(args.url) + "\"}"
    else:
        queryHeaders['content-type'] = "application/json"
        urlToAudio = str(input("Enter a URL of an audio file."))
        payload = "{\"url\":\"" + str(urlToAudio) + "\"}"

    queryHeaders['Authorization'] = "Basic " + str(parseCredentials(args))

    apiRequest = "/v2/listen?" + parseQuery(args)

    conn.request("POST", apiRequest, payload, queryHeaders)

    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))

def readLocalTranscript(localTranscript):
    rawTranscript = open(localTranscript)
    jsonTranscript = json.load(rawTranscript)
    rawTranscript.close()
    return jsonTranscript

    
def parseTranscript(queryData, args):
    returnedData = {}
    if args.verbose:
        returnedData = queryData
    elif args.search:
        returnedData['transcript'] = queryData['results']['channels'][0]['alternatives'][0]['transcript']
        returnedData['search'] = queryData['results']['channels'][0]['search']
    else:
        justTranscript = queryData['results']['channels'][0]['alternatives'][0]['transcript']
        returnedData = justTranscript

    print(json.dumps(returnedData, indent=2, sort_keys=False))

    return returnedData


def main():
    args = parse_args()

    if args.output_folder: 
        outputFolder = args.output_folder
    else: 
        outputFolder = "./transcripts/"

    if not os.path.isdir(outputFolder):
        os.mkdir(outputFolder)

    if args.local and not (args.input_dir or args.input_file):
        print("You need to specify a file(-f) or director(-d) for --local processing.")

    if args.input_dir:
        for file in os.listdir(args.input_dir):
            inputFileName = os.path.join(args.input_dir, file)
            outputFileName = str(os.path.join(outputFolder, file)) + ".json"
            if not args.local:
                print ("Processing: " + str(inputFileName))
                outputData = getTranscipt(args, inputFileName)
                outputFile = open(outputFileName, "w")
                outputFile.write(json.dumps(outputData))
                outputFile.close()
                parseTranscript(outputData, args)
            else:
                print("\nReading from {}".format(inputFileName))
                parseTranscript(readLocalTranscript(inputFileName), args)
    elif args.input_file:
        if not args.local:
            parseTranscript(getTranscipt(args), args)
        else:
            parseTranscript(readLocalTranscript(args.input_file), args)
    elif args.url:
        parseTranscript(getTranscipt(args), args)

    else:       
        print("No transciption files specified.\nUse -h to read more about this script.")
        


if __name__ == "__main__":
    main()
