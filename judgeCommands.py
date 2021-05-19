import os
import shutil
import random

from discord.ext import commands
from dotenv import load_dotenv

from baseBot import *
from Tournament import * 


commandSnippets["admin-register"] = "- admin-register : Registers a player for a tournament"
commandCategories["admin-registration"].append("admin-register")
@bot.command(name='admin-register')
async def adminAddPlayer( ctx, tourn = "", plyr = "" ):
    tourn = tourn.strip()
    plyr  = plyr.strip()
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "" or plyr == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament and player in order to add someone to a tournament.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findGuildMember( ctx.guild, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, there is not a member of this server whose name nor mention is "{plyr}".' )
        return
    
    if member.id in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, {plyr} is already registered for {tourn}.' )
        return

    message = await tournaments[tourn].addPlayer( member, admin=True )
    tournaments[tourn].players[member.id].saveXML( )
    await ctx.send( message )


commandSnippets["admin-add-deck"] = "- admin-add-deck : Registers a deck for a player in a tournament" 
commandCategories["admin-registration"].append("admin-add-deck")
@bot.command(name='admin-add-deck')
async def adminAddDeck( ctx, tourn = "", plyr = "", ident = "" ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()
    ident = ident.strip()
    
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "" or plyr == "" or ident == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a player, a deck identifier, and a decklist in order to add a deck for someone.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return
    
    if not member.id in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in {tourn}. Make sure they are registered or that they have not dropped.' )
        return
    
    index = ctx.message.content.find( ident ) + len(ident)
    decklist = re.sub( "^[^A-Za-z0-9\w\/]+", "", ctx.message.content[index:].replace('"', "") ).strip() 
    decklist = re.sub( "[^A-Za-z0-9\w\/]+$", "", decklist )
    
    if decklist == "":
        await ctx.send( f'{ctx.message.author.mention}, not enough information provided: Please provide your deckname and decklist to add a deck.' )
        return
    
    message = ""
    try:
        message = tournaments[tourn].addDeck( member.id, ident, decklist, admin=True )
    except:
        await ctx.send( f'{ctx.message.author.mention}, there was an error while processing the deck list. Make sure you follow the instructions for submitting a deck. To find them, use "!squirebot-help add-deck".' )

    tournaments[tourn].players[member.id].saveXML( )
    await ctx.send( message )


commandSnippets["admin-remove-deck"] = "- admin-remove-deck : Removes a deck for a player in a tournament" 
commandCategories["admin-registration"].append("admin-remove-deck")
@bot.command(name='admin-remove-deck')
async def adminRemoveDeck( ctx, tourn = "", plyr = "", ident = "" ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()
    ident = ident.strip()

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "" or plyr == "" or ident == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a player, a deck identifier, and a decklist in order to add a deck for someone.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return

    if not member.id in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    deckName = tournaments[tourn].players[member.id].getDeckIdent( ident )
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, it appears that {plyr} does not have a deck whose name nor hash is "{ident}" registered for {tourn}.' )
        return
        
    if await hasCommandWaiting( ctx, ctx.message.author.id ):
        del( commandsToConfirm[ctx.message.author.id] )

    commandsToConfirm[ctx.message.author.id] = ( getTime(), 30, tournaments[tourn].players[member.id].removeDeckCoro( deckName, ctx.message.author.mention ) )
    await ctx.send( f'{ctx.message.author.mention}, in order to remove the deck {deckName} from {member.mention}, confirmation is needed. Are you sure you want to remove the deck (!yes/!no)?' )


commandSnippets["list-players"] = "- list-players : Lists all player (or the number of players) in a tournament " 
commandCategories["admin-misc"].append("list-players")
@bot.command(name='list-players')
async def adminListPlayers( ctx, tourn = "", num = "" ):
    tourn = tourn.strip()
    num   = num.strip().lower()
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament in order to list the players.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    if len( tournaments[tourn].players ) == 0:
        await ctx.send( f'{ctx.message.author.mention}, there are no players registered for the tournament {tourn}.' )
        return
    
    playerNames = [ tournaments[tourn].players[plyr].discordUser.mention for plyr in tournaments[tourn].players if tournaments[tourn].players[plyr].isActive() and not tournaments[tourn].players[plyr].discordUser is None ]
    if num == "n" or num == "num" or num == "number":
        await ctx.send( f'{ctx.message.author.mention}, there are {len(playerNames)} active players in {tourn}.' )
        return
    else:
        newLine = "\n\t- "
        await ctx.send( f'{ctx.message.author.mention}, the following are all active players registered for {tourn}:' )
        message = f'{newLine}{newLine.join(playerNames)}'
        for msg in splitMessage( message ):
            await ctx.send( msg )
    

commandSnippets["player-profile"] = "- player-profile : Lists out a player's profile, including decks names, matches, and status" 
commandCategories["admin-misc"].append("player-profile")
@bot.command(name='player-profile')
async def adminPlayerProfile( ctx, tourn = "", plyr = "" ):
    tourn = tourn.strip()
    plyr  = plyr.strip()
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament in order to list the players.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role "{tourn} Player". Please verify that they have registered.' )
        return

    if not member.id in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    await ctx.send( content=f'{ctx.message.author.mention}, the following is the profile for {plyr}:', embed=tournaments[tourn].getPlayerProfileEmbed(member.id) )


commandSnippets["admin-match-result"] = "- admin-match-result : Record the result of a match for a player" 
commandCategories["admin-playing"].append("admin-match-result")
@bot.command(name='admin-match-result')
async def adminMatchResult( ctx, tourn = "", plyr = "", mtch = "", result = "" ):
    tourn  = tourn.strip()
    plyr   = plyr.strip()
    mtch   = mtch.strip()
    result = result.strip()
    
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role "{tourn} Player". Please verify that they have registered.' )
        return
    
    if not member.id in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number. Please specify a match number as a number.' )
        return
    
    if mtch > len(tournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
        
    Match = tournaments[tourn].players[member.id].getMatch( mtch )
    if Match.matchNumber == -1:
        await ctx.send( f'{ctx.message.author.mention}, {member.mention} is not a player in Match #{mtch}. Double check the match number.' )
        return
        
    message = await tournaments[tourn].recordMatchResult( member.id, result, mtch, admin=True )
    Match.saveXML( )
    await ctx.send( message )
    

commandSnippets["admin-confirm-result"] = "- admin-confirm-result : Confirms the result of a match on a player's behalf" 
commandCategories["admin-playing"].append("admin-confirm-result")
@bot.command(name='admin-confirm-result')
async def adminConfirmResult( ctx, tourn = "", plyr = "", mtch = "" ):
    tourn  = tourn.strip()
    plyr   = plyr.strip()
    mtch   = mtch.strip()
    
    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, match number, player, and result in order to remove a player from a match.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role "{tourn} Player". Please verify that they have registered.' )
        return
    
    if not member.id in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number. Please specify a match number using digits.' )
        return
    
    if mtch > len(tournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
        
    Match = tournaments[tourn].players[member.id].getMatch( mtch )
    if Match.matchNumber == -1:
        await ctx.send( f'{ctx.message.author.mention}, {member.mention} is not a player in Match #{mtch}. Double check the match number.' )
        return
    
    if Match.isCertified( ):
        await ctx.send( f'{ctx.message.author.mention}, match #{mtch} is already certified. There is no need confirm the result again.' )
        return
    if member.id in Match.confirmedPlayers:
        await ctx.send( f'{ctx.message.author.mention}, match #{mtch} is not certified, but {plyr} has already certified the result. There is no need to do this twice.' )
        return
    
    message = await tournaments[tourn].confirmResult( member.id, Match.matchNumber )
    Match.saveXML( )
    await ctx.send( f'{ctx.message.author.mention}, {message}.' )



commandSnippets["give-time-extension"] = "- give-time-extension : Give a match more time in their match" 
commandCategories["admin-playing"].append("give-time-extension")
@bot.command(name='give-time-extension')
async def giveTimeExtension( ctx, tourn = "", mtch = "", t = "" ):
    tourn = tourn.strip()
    mtch  =  mtch.strip()
    t     =  t.strip()

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "" or mtch == "" or t == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a match number, and an amount of time.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number correctly. Please specify a match number using digits.' )
        return
    
    if mtch > len(tournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
    
    if tournaments[tourn].matches[mtch - 1].stopTimer:
        await ctx.send( f'{ctx.message.author.mention}, match #{mtch} does not have a timer set. Make sure the match is not already over.' )
        return
    
    try:
        t = int( t )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide an amount of time correctly. Please specify a match number using digits.' )
        return
    
    if t < 1:
        await ctx.send( f'{ctx.message.author.mention}, you can not give time extension of less than one minute in length.' )
        return
        
    tournaments[tourn].matches[mtch - 1].giveTimeExtension( t*60 )
    tournaments[tourn].matches[mtch - 1].saveXML( )
    for plyr in tournaments[tourn].matches[mtch - 1].activePlayers:
        await tournaments[tourn].players[plyr].discordUser.send( content=f'Your match (#{mtch}) in {tourn} has been given a time extension of {t} minute{"" if t == 1 else "s"}.' )
    await ctx.send( f'{ctx.message.author.mention}, you have given match #{mtch} a time extension of {t} minute{"" if t == 1 else "s"}.' )



commandSnippets["admin-decklist"] = "- admin-decklist : Posts a decklist of a player" 
commandCategories["admin-misc"].append( "admin-decklist" )
@bot.command(name='admin-decklist')
async def adminPrintDecklist( ctx, tourn = "", plyr = "", ident = "" ):
    tourn = tourn.strip()
    plyr  =  plyr.strip()
    ident = ident.strip()

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "" or plyr == "" or ident == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a player, a deck identifier, and a decklist in order to add a deck for someone.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    member = findPlayer( ctx.guild, tourn, plyr )
    if member == "":
        await ctx.send( f'{ctx.message.author.mention}, a player by "{plyr}" could not be found in the player role for {tourn}. Please verify that they have registered.' )
        return

    if not member.id in tournaments[tourn].players:
        await ctx.send( f'{ctx.message.author.mention}, a user by "{plyr}" was found in the player role, but they are not active in the tournament "{tourn}". Make sure they are registered or that they have not dropped.' )
        return
    
    deckName = tournaments[tourn].players[member.id].getDeckIdent( ident )
    if deckName == "":
        await ctx.send( f'{ctx.message.author.mention}, {plyr} does not have any decks registered for {tourn}.' )
        return

    await ctx.send( embed = await tournaments[tourn].players[member.id].getDeckEmbed( deckName ) )


commandSnippets["match-status"] = "- match-status : View the currect status of a match" 
commandCategories["admin-misc"].append("match-status")
@bot.command(name='match-status')
async def matchStatus( ctx, tourn = "", mtch = "" ):
    tourn = tourn.strip()
    mtch  =  mtch.strip()

    if await isPrivateMessage( ctx ): return

    if not await isAdmin( ctx ): return
    if tourn == "" or mtch == "":
        await ctx.send( f'{ctx.message.author.mention}, you did not provide enough information. You need to specify a tournament, a match number, and an amount of time.' )
        return
    if not await checkTournExists( tourn, ctx ): return
    if not await correctGuild( tourn, ctx ): return
    if await isTournDead( tourn, ctx ): return
    
    try:
        mtch = int( mtch )
    except:
        await ctx.send( f'{ctx.message.author.mention}, you did not provide a match number correctly. Please specify a match number using digits.' )
        return
    
    if mtch > len(tournaments[tourn].matches):
        await ctx.send( f'{ctx.message.author.mention}, the match number that you specified is greater than the number of matches. Double check the match number.' )
        return
    
    await ctx.send( f'{ctx.message.author.mention}, here is the status of match #{mtch}:', embed=tournaments[tourn].getMatchEmbed( mtch-1 ) )



