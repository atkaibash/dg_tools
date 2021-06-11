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
        A wrapper for the Deepgram transcription API. More info on the API available at: 
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
        dest="storeCreds",
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
        "--keep",
        "-k",
        dest="keep",
        default=False,
        action="store_true",
        help="Keep existing transcripts.",
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
        help="Insert any additional parameters in one big string Ex. 'diarize=true&numerals=true'",
    )
    p.add_argument(
        "--search",
        dest="search",
        action="append",
        default=[],
        help="Search the audio file for the given words. If --local is set, look only for previously searched words. \n{}search".format(docsURL),
    )
    p.add_argument(
        "--search-threshold",
        "-st",
        dest="search_threshold",
        action="store",
        type=float,
        default=False,
        help="Sets a threshold to only return searches results with confidence values above the threshold. Values should be between [0-1].",
    )
    p.add_argument(
        "--fqdn",
        dest="fqdn",
        action="store",
        default="brain.deepgram.com",
        help="Set the FQDN for your API queries. Default is brain.deepgram.com",
    )
    args = p.parse_args()

    if args.local and not (args.input_dir or args.input_file):
        print("You need to specify a file(-f) or director(-d) for --local processing.")

    return args


def parseCredentials(args):
    '''
    Look for stored credentials, if none found and none in the command, prompt for
    username and password.
    If --store-credentials set, then make some effort to set an environment variable
    called DG_AUTH. 
    Returns a base64 encoded string from username:password.
    ''' 
    usr = ""
    passwd = ""
    
    if not args.storeCreds and "DG_AUTH" in os.environ:
        return os.environ["DG_AUTH"]

    if args.user:
        usr = args.user
    else:
        usr = input("Username:")
 
    if not args.password:
        passwd = str(getpass.getpass("Password:"))
    else:
        passwd = str(args.password)

    # Build the "username:auth" string and then encode it. 
    rawAuthBytes = str(str(usr) + ":" + str(passwd)).encode("utf-8")
    encodedAuth = base64.b64encode(rawAuthBytes).decode("utf-8")
    # Check if user set store creds and try to save the encoded auth to an environment variable. 
    if args.storeCreds:
        shell = os.environ['SHELL']  
        if  "zsh" in shell:
            print ("Saving encoded credentials to DG_AUTH and to your zsh profile.")
            try:
                os.system("echo 'export DG_AUTH={}' >> ~/.zshenv".format(encodedAuth))
            except:
                print ("Unable to save credentials, please add DG_AUTH={} to environment variable".format(encodedAuth))
            os.system('export DG_AUTH={}'.format(encodedAuth)) 
            if  "DG_AUTH" not in os.environ:
                print ("We encountered an issue getting DG_AUTH into this session\
                it was saved to your profile and will appear when you restart the terminal.")

        elif "bash" in shell: 
            print ("Saving encoded credentials to DG_AUTH and to your bash profile.")
            try:
                os.system("echo 'export DG_AUTH={}' >> ~/.bash_profile".format(encodedAuth))
            except:
                print ("Unable to save credentials, please add DG_AUTH={} to environment variable".format(encodedAuth))
            os.system('export DG_AUTH={}'.format(encodedAuth))
        else:
            print("I'm not sure what your shell is. You can add DG_AUTH={} to your\
            environment variables".format(encodedAuth))
        

    return encodedAuth


def parseQuery(args):
    '''
    Walk through args from the command line that pertain to API queries.
    ''' 
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
        for searchString in args.search:
            apiParams += str(apiChar + "search=" + str(searchString))
        apiChar ="&"
    if args.params:
        apiParams += str(apiChar + args.params)
    return apiParams


def getTranscipt(args, fileFromDir=False):
    '''
    Build the API call to get the transcripts and return as a JSON object.
    '''
    conn = http.client.HTTPSConnection(str(args.fqdn))
    queryHeaders ={}
    # Parse the input type and build the content-type and payload.
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

    queryHeaders['Authorization'] = "Basic " + str(creds)
    apiRequest = "/v2/listen?" + parseQuery(args)
    conn.request("POST", apiRequest, payload, queryHeaders)

    # Submit the API call  
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))

def saveTranscript(transcriptData, outputFileName):
    # Helper function to write transcripts to disk. 
    outputFile = open(outputFileName, "w")
    outputFile.write(json.dumps(transcriptData))
    outputFile.close()


def readLocalTranscript(localTranscript):
    # Helper function to read transcripts from disk. 
    rawTranscript = open(localTranscript)
    jsonTranscript = json.load(rawTranscript)
    rawTranscript.close()
    return jsonTranscript

    
def parseTranscript(queryData, args):
    '''
    Parse a transcript and do one of the following:
    1) Return the full output. 
    2) Return the transcrpit and the requested serach terms.
    3) Just return the transcrpit.
    '''
    returnedData = {}
    searchData = {}
    if args.verbose: # Return the full transcript.
        returnedData = queryData
    elif args.search: # Try to handle the supplied search terms. 
        # Still grab the transcirpt.
        returnedData['transcript'] = queryData['results']['channels'][0]['alternatives'][0]['transcript']
        # Try to pull the search data. 
        try:
            searchData['search'] = queryData['results']['channels'][0]['search']
        except:
            print ("No search data found for transcript.")
            return
        if args.search == ['all']: # Value for when you want all search terms returned.
            returnedData['search'] = searchData['search']
        else: # Otherwise parse the requested search terms in the current transcript. 
            for searchTermData in searchData['search']: 
                thisWord = searchTermData['query'] # Go through each stored search term.
                if thisWord in args.search: # Check if the user requested it. 
                    if args.search_threshold: # Check if search_threshold is set. 
                        searchWordHits = { "hits":[]} # If so, make a temporary empty dict.
                        for hit in searchTermData['hits']: # Go through all hits. 
                            if hit['confidence'] >= args.search_threshold: # Check if confidence is above threshold.
                                searchWordHits['hits'].append(hit) # If so append to temp hit dict. 
                        if len(searchWordHits['hits']) > 0: # Check that we got atleast 1 hit.
                            returnedData[thisWord]= searchWordHits # If so add the temp list to final results.
                    else:
                        returnedData[thisWord] = searchTermData # If search_threshold was not set return all hits.                
    else: # Return just the transcript.
        justTranscript = queryData['results']['channels'][0]['alternatives'][0]['transcript']
        returnedData = justTranscript

    print(json.dumps(returnedData, indent=2, sort_keys=False))
 
    return returnedData


def main():
    '''
    1) Parse Args
    2) Set the output folder.
    5) Store creds.
    6) Parse the input for files.
        a) Input dir
        b) Input file
        c) URL

    '''
    args = parse_args()

    if args.output_folder: 
        outputFolder = args.output_folder
    else: 
        outputFolder = "./transcripts/"

    if not os.path.isdir(outputFolder):
        os.mkdir(outputFolder)
 
    if not args.local:
        global creds
        creds = parseCredentials(args)

    if args.input_dir:
        for file in os.listdir(args.input_dir):
            inputFileName = os.path.join(args.input_dir, file)
            outputFileName = str(os.path.join(outputFolder, file)) + ".json"
            if args.local: 
                print("\nReading {} from disk".format(inputFileName)) 
                parseTranscript(readLocalTranscript(inputFileName), args)
            elif os.path.isfile(outputFileName) and args.keep:
                print("Transcript already exists for audio file, and --keep is set.")
            else:
                print ("\nProcessing: " + str(inputFileName))
                outputData = getTranscipt(args, inputFileName)
                saveTranscript(outputData, outputFileName)
                parseTranscript(outputData, args) 
    
    if args.input_file:
        if args.local:
            parseTranscript(readLocalTranscript(args.input_file), args)
        else:
            print ("\nProcessing: " + str(args.input_file))
            dirs, inputFileName = os.path.split(args.input_file)
            outputFileName = str(os.path.join(outputFolder, inputFileName) + ".json")
            outputData = getTranscipt(args, args.input_file)
            saveTranscript(outputData, outputFileName)
            parseTranscript(outputData, args)
    
    if args.url:
        outputData = parseTranscript(getTranscipt(args), args)
        if arg.output_folder:
            outputFileName = str(arg.output_folder + ".json")
            saveTranscript(outputData,outputFileName)

        

if __name__ == "__main__":
    main()
