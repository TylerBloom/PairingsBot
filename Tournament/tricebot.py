import zipfile
import urllib.parse
import tempfile
import requests
import re

class GameMade:
    def __init__(self, success: bool, gameID: int, replayName: str):
        self.success = success
        self.gameID = gameID
        self.replayName = replayName

class ChangePlayerInfo:
    def __init__(self, success: bool, playerFound: bool=True, gameFound: bool=True, error: bool=False):
        self.success = success
        self.playerFound = playerFound
        self.gameFound = gameFound
        self.error = error

class TriceBot:
    # Set externURL to the domain address and apiURL to the loopback address in LAN configs
    def __init__(self, authToken: str, apiURL: str="https://0.0.0.0:8000", externURL: str=""):
        self.authToken = authToken
        self.apiURL = apiURL
        
        if (externURL == ""):
            self.externURL = self.apiURL
        else:
            self.externURL = externURL
        
    # verify = false as self signed ssl certificates will cause errors here
    def req(self, urlpostfix: str, data: str) -> str:
        print(data)
        resp = requests.get(f'{self.apiURL}/{urlpostfix}', timeout=7.0, data=data,  verify=False).text
        print(resp)
        return resp
        
    def checkauthkey(self):
        return self.req("api/checkauthkey", self.authToken) == "1"
    
    def getDownloadLink(self, replayName: str) -> str:
        return f'{self.externURL}/{replayName}'
    
    # Returns the zip file which contains all of the downloaded files
    # Returns none if the zip file would be empty or if there was an IOError
    def downloadReplays(self, replayURLs, replaysNotFound = []):                
        # Download all the replays
        replayStrs = []
        
        # Iterate over
        for replayURL in replayURLs:
            try:
                res = self.req("api/updateplayerinfo", body)
                name = urllib.parse.unquote(split[len(split) - 1])
                if res == "error 404" or re.match("Not found \[.*\]", res) or re.match("<!DOCTYPE html>.*", res):
                    # Error file not found
                    replaysNotFound.append(name)
                else:
                    # Create a temp file and write the data
                    split = replayURL.split("/")
                    
                    replayStrs.append(res)                    
                    replayNames.append(name)
            except OSError as exc:
                # Network issues
                print("[TRICEBOT ERROR]: Netty error")
                replaysNotFound.append(replayURL)
        
        # Create zip file then close the temp files
        try:
            if (len(replayStrs) == 0):
                return None
            
            zipf = zipfile.ZipFile(tempfile.TemporaryFile("wb+", 'w+'), zipfile.ZIP_DEFLATED, suffix="tricebot.py", prefix="replaydownloads")
            for i in range(0, len(replayStrs)):
                name = replayStrs[i]
                replayStr = replayNames[i]            
                ziph.writestr(replayStr, name)
            return zipf
        except IOError as exc:
            return None
    
    # Returns a ChangePlayerInfo object that contains the state of the request
    def changePlayerInfo(self, gameID: int, oldPlayerName: str, newPlayerName: str) -> str:
        body  = f'authtoken={self.authToken}\n'
        body += f'oldplayername={oldPlayerName}\n'
        body += f'newplayername={newPlayerName}\n'
        body += f'gameid={gameID}'
        
        res = ""
        try:
            res = self.req("api/updateplayerinfo", body)
        except OSError as exc:
            #Network issues
            print("[TRICEBOT ERROR]: Netty error")
            res = "network error"
            
        if res == "success":
            return ChangePlayerInfo(True)
        elif res == "error game not found":
            return ChangePlayerInfo(False, False, False)
        elif res == "error player not found":
            return ChangePlayerInfo(False, False, True)
        else:
            return ChangePlayerInfo(False, False, False, True)
    
    # 1 if success
    # 0 auth token is bad, error 404 or network issue
    # -1 game not found
    def disablePlayerDeckVerificatoin(self, gameID: str) -> int:
        body  = f'authtoken={self.authToken}\n'
        body += f'gameid={gameID}'
        
        res = ""
        try:
            res = self.req("api/disableplayerdeckverification", body)
        except OSError as exc:
            #Network issues
            print("[TRICEBOT ERROR]: Netty error")
            res = "network error"
            return 0
            
        if res == "success":
            return 1
        elif res == "error 404" or "invalid auth token":
            return 0
        elif res == "game not found":
            return -1
        return 0
    
    #  1 if success
    #  0 auth token is bad or error404 or network issue
    # -1 if player not found
    # -2 if an unknown error occurred
    def kickPlayer(self, gameID: int, name: str) -> int:
        body  = f'authtoken={self.authToken}\n'
        body += f'gameid={gameID}\n'
        body += f'target={name}'        
        
        try:
            message = self.req("api/kickplayer", body)
        except OSError as exc:
            # Network issues
            print("[TRICEBOT ERROR]: Netty error")
            return 0
        
        # Check for server error
        if (message == "timeout error" or message == "error 404" or message == "invalid auth token"):        
            return 0        
        if (message == "success"):
            return 1
        elif (message == "error not found"):
            return -1
        
        return -2
    
    def createGame(self, gamename: str, password: str, playercount: int, spectatorsallowed: bool, spectatorsneedpassword: bool, spectatorscanchat: bool, spectatorscanseehands: bool, onlyregistered: bool, playerdeckverification: bool, playernames, deckHashes):
        if len(playernames) != len(deckHashes):
            GameMade(False, -1, -1) # They must the same length dummy!
            
        body  = f'authtoken={self.authToken}\n'
        body += f'gamename={gamename}\n'
        body += f'password={password}\n'
        body += f'playerCount={playercount}\n'        
        body += f'spectatorsAllowed={int(spectatorsallowed)}\n'            
        body += f'spectatorsNeedPassword={int(spectatorsneedpassword)}\n'        
        body += f'spectatorsCanChat={int(spectatorscanchat)}\n'        
        body += f'spectatorsCanSeeHands={int(spectatorscanseehands)}\n'        
        body += f'onlyRegistered={int(onlyregistered)}\n'   
        body += f'playerDeckVerification={int(playerdeckverification)}\n'
        
        if playerdeckverification:
            for i in range(0, len(playernames)):
                if playernames[i] == "" or playernames[i] == None: # No name
                    body += f'playerName=*\n'
                else:
                    body += f'playerName={playernames[i]}\n'
                    if len(deckHashes[i]) == 0:
                        body += f'deckHash=*\n'
                    else:
                        for deckHash in deckHashes[i]:
                            body += f'deckHash={deckHash}\n'
        
        try:
            message = self.req("api/creategame", body)   
            print(message)
        except OSError as exc:
            #Network issues
            print("[TRICEBOT ERROR]: Netty error")
            return GameMade(False, -1, "")
            
        # Check for server error
        if (message.lower() == "timeout error") or (message.lower() == "error 404") or (message.lower() == "invalid auth token"):
            #Server issues         
            print("[TRICEBOT ERROR]: " + message)
            return GameMade(False, -1, "")
        
        # Try to parse the message
        lines = message.split("\n")
        gameID: int = -1
        replayName: str = ""
        
        # Parse line for line
        for line in lines:
            parts = line.split("=")
            
            # Check length
            if len(parts) >= 2 :            
                tag = parts[0]
                value = ""
                for i in range(1, len(parts)):
                    value += parts[i]
                    if i != len(parts) - 1:
                        value += "="
                    
                if tag == "gameid":
                    # There has to be a better way to do this
                    try:
                        gameID = int(value)
                    except:
                        # Error checked at end
                        pass
                elif tag == "replayName":
                    replayName = urllib.parse.quote(value)
                # Ignore other tags
            # Ignores lines that have no equals in them
        
        # Check if there was an error
        success = (gameID != -1) and (replayName != "")
        print(success)
        return GameMade(success, gameID, replayName)
