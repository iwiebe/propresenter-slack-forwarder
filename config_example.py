# this was the easiest way to bundle the example file into the executable...
example = """
[bot]
bot-token = "" # optional key, if you dont fill this in itll pull from the configured network
app-token = "" # also optional
listen-channel = "" # the slack channel to listen to
ignore-numbers = ["5555", "7777", ""] # these won't be sent automatically

[propresenter]
v = 6 # or 7
host = "127.0.0.1"
port = 55184
password = ""
batch-wait-time = 10 # how long to wait for multiple numbers before processing them
batch-max-count = 3 # how many numbers to batch together
expire-time = 45
# propresenter 7 decided it doesnt need to send feedback for events, 
# so we have no way of knowing if someone presses hide, or if someone takes the screen manually.
# so for pro7, we'll just guess

[network] # retrieve credentials
target = ""
simpleauth-pass = ""
"""