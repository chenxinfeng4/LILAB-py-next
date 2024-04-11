mkvfiles=`ls *.mkv`
echo "$mkvfiles" | awk '{sub(/\.mkv$/,"");print}' | \
    xargs -n 1 -I {} ffmpeg -y -i {}.mkv -c copy {}.mp4

echo "$mkvfiles" | xargs -n 1 -I {} rm {}
