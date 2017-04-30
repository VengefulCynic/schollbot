import os
import time
import markovify
from slackclient import SlackClient


# starterbot's ID as an environment variable
#BOT_ID = os.environ.get("BOT_ID")
BOT_ID = 'U4M86BLHK'

# constants
AT_BOT = "<@" + BOT_ID + ">"

# instantiate Slack client
bottoken = os.environ.get("SLACK_BOT_TOKEN")
slack_client = SlackClient(bottoken)

text_model = None

def get_ready():
    with open("scholl_blog") as f:
        text = f.read()
    with open("schollbot_text") as f:
        text += f.read()
    with open("schollbot_successes") as f:
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

def handle_reaction(command, channel):
    channel_status = slack_client.api_call("channels.info", channel=channel)
    if not channel_status['ok'] and "channel_not_found" in channel_status['error']:
        #possibly a private channel?
        channel_status = slack_client.api_call("groups.info", channel=channel)
        if channel_status['ok']:
            print("calling groups.history, channel: " + channel)
            print("latest: " + command)
            message = slack_client.api_call("groups.history", channel=channel,
                                    latest=command, inclusive=True, count=1)
        else:
            print("ERROR!")
            print(message)
            return None
    else:
        print("calling channels.history, channel: " + channel)
        print("latest: " + command)
        message = slack_client.api_call("channels.history", channel=channel,
                                        latest=command, inclusive=True, count=1)
    if message and 'messages' in message:
        for messages in message['messages']:
            if 'text' in messages:
                with open("schollbot_successes", "a") as writefile:
                    writefile.writelines('\n' + messages['text'])
                    print("Just wrote to file: " + messages['text'])


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'type' in output:
                if output and 'text' in output and AT_BOT in output['text']:
                    # return text after the @ mention, whitespace removed
                    return 'message', \
                           output['text'].split(AT_BOT)[1].strip().lower(), \
                           output['channel']
                elif 'reaction_added' in output['type'] and BOT_ID in output['item_user']:
                        print("reaction added")
                        print(output)
                        return 'reaction_added', \
                               output['item']['ts'], \
                               output['item']['channel']
                elif 'star_added' in output['type'] and BOT_ID in output['item_user']:
                        print("star added")
                        print(output)
                        return 'star_added', \
                               output['item']['ts'], \
                               output['item']['channel']
    return None, None, None


def handle_invite(channel):
    slack_client.api_call("chat.postMessage", channel=channel, text="Schollbot is here bitches!!!", as_user=True)

if __name__ == "__main__":
    get_ready()
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        #print("Schollbot is here bitches!!!")
        while True:
            event, command, channel = parse_slack_output(slack_client.rtm_read())
            if event:
                if event == 'message' and command and channel:
                    handle_command(command, channel)
                elif event == 'reaction_added' and command and channel:
                    handle_reaction(command, channel)
                elif event == 'star_added' and command and channel:
                    handle_reaction(command, channel)
                else:
                    handle_invite(channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
