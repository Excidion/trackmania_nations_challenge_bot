# TrackMania Nations Challenge Bot
## Concept
Telegram chatbot to serve as a moderator to a weekly challenge in the video game TrackMania Nations.
The rules are simple:
+ Every week a track is chosen for the participants to race on.
This track is hosted on an online multiplayer server for the entirety of the week.

+ A weeks winner is the one to drive the fastest time over the course of the week.
All times have to be scored on the before mentioned game server.
On 0:00:00 every monday the game server shuts down and a winner is announced.

+ The overall winner is determined by summing the personal bests for every track.
The participant with the lowest overall time wins.

+ Participants who fail to score at any given track will be assigned a time that has been beaten by all other participants for that track.
This time is chosen from the *medal* times of that track.


## Features
The bot will provide the following services for the proceeding of the challenge:

+ Announce rankings at the end of each week.

+ Inform participants about changes in this weeks rankings.

+ Show graphs and tables of weekly and overall rankings when asked.

+ Help players connect to the game server.

+ Registration of player names to be displayed in rankings and graphs.

## Setup
### Telegram

### TrackMania
This bot requires a database of tracks and player times to connect to that is continuously filled with the times scored on the game server.
Since TrackMania Nations is an old game this will require some setup work with legacy technology that proved notoriously tricky to handle.
It is therefore strongly adviced to use the docker images created by [@fanyx](https://github.com/fanyx) for this very project.
Check out his work:

+ [fanyx/docker-tmserver](https://github.com/fanyx/docker-tmserver) for the online game server.

+ [fanyx/docker-xaseco](https://github.com/fanyx/docker-xaseco) for the database server.

+ [fanyx/docker-tmnationsbot](https://github.com/fanyx/docker-tmnationsbot) for a containerised version of this bot.
