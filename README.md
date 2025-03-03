# Upset-Bot
Discord bot that uses the upset tracker to post to discord

##### What is the goal?
The goal of this bot is to use the api for start.gg to get the seeding and sets of a tournament.
The bot then takes this data and returns all of the sets where a lower seed beats a higher seed, known as an upset.
After getting this data, the bot then posts it to a discord channel.

### Functions


## Issues
 - After the first tournament test, I found that if a set is miseported and is an upset, it will get posted, this is fine, however, if the set is then fixed, then the previous upset in the list is then called. This is an issue, because it will send the last upset again.
     - I put the messages into a set and if they are in the set, then they are not posted.

 - If a new phase is missing a player, due to the previous phase not being finished, then it will return a null object, breaking the bot.
     - If there is not an entrant, it just continues now

 - If there are multiple phases of an entire event, the seeding changes between the events. I want to use the seeding from the initial phase.
     - I query the event first for the phase Ids, then query the initial phase for the seeding.
     - I then query each phase for the sets to get upsets. This solves the seeding issue and allows me to query an entire event off of 1 link.
