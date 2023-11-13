#!/bin/bash
# Greeting message: 'Welcome to the marmoset tracker!'
curl http://10.50.60.6:8089/

# Camera position json file: {cam0:[K, dist, t, R], ...}
curl http://10.50.60.6:8089/ba_poses

# Get the real time updating marmoset position: [timestamp, [iframe, position_3d]]
curl http://10.50.60.6:8089/com3d
