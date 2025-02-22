This is a script in python to process roms collection for different uses. I started working on this due to influence from [SpaceGhost1993's Tool](https://github.com/SpaceGhost1993/DEM-Wiiflow-Tools), great tool but there were some stuff I just didnt prefer, so I decided to make an all in one tool. The idea is to have it all in one go or system by system if you choose.

# Main Menu
This is where you would select where the files are going. Only `Nintendo Wii` works currently though. The mappings in `Master.txt` are referenced by which you choose (ie. `Nintendo Wii` will look for mappings with prefix `- wii`). Im hoping to be able to rename the folders dynamically based on which system they are being put on (ie. For Sega CD if you select `Wii` it will use the naming `ROMS\Mega CD` and then selecting `rpi` would name it `roms\segacd`). Still learning how to do this so it may be a while...
## Raspberry Pi
Everyone loves Raspberry Pi's right... right?

Under construction ATM...
## Nintendo Wii
Looks for the folder ROMS and the naming scheme of Wiiflow.
### Match cover art to games
This compares `.png` file names located in `ROMS\System\cover art` to the games in `ROMS\system name` with a `75%`, then copies the `.png` file and renames it `gamename.gameext.png`. There is also promt to move unmatched games to `unmatched cover art`.
### Undo matching of cover art
This moves files in `unmatched cover art` to `Roms\system name` then deletes `unmatched cover art` and `renamed cover art` folders.
### Copy files to drive
Prompts to select a drive to copy to then gives a list of systems that have files in both `renamed cover art` and `ROMS\system name`. After selecting a system to transfer it will then transfer the local files to selected drive.  `All Systems` is an option too.
### Delete files from drive
Prompts to select a drive to copy to then gives a list of systems that have files in both `wiiflow\boxart\system name` and `ROMS\system name`. After selecting a system it will then delete the contents of those folders. `All Systems` is an option too.
### Sort files
This sorts the the files if they have a `region` tag. I have it set to remove `PAL` games. Im looking into how to exclude handhelds from this as those dont count.
### Unsort files
This reverses the `region` sort adding `PAL` games back to `ROMS\system name
## OG XBOX
I have very little experience in XBOX stuff so I'm interested on what I can actually add here

Under construction ATM...
