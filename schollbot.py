import os
import time
import markovify
from slackclient import SlackClient


# starterbot's ID as an environment variable
#BOT_ID = os.environ.get("BOT_ID")
BOT_ID = 'U4NCZDUJJ'

# constants
AT_BOT = "<@" + BOT_ID + ">"

# instantiate Slack client
bottoken = os.environ.get("schollbot")
slack_client = SlackClient(bottoken)

text_model = None

def get_ready():
    with open("scholl_blog") as f:
        text = f.read()
    with open("schollbot_text") as f:
        text += f.read()
    global text_model
    text_model = markovify.Text(text)
    


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    global text_model
    response = text_model.make_short_sentence(200)
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


def handle_invite(channel):
    slack_client.api_call("chat.postMessage", channel=channel, text="Schollbot is here bitches!!!", as_user=True)

if __name__ == "__main__":
    get_ready()
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        #print("Schollbot is here bitches!!!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            else:
                handle_invite(channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
