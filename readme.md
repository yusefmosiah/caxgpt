# Choir

Aspirationally, Choir Chat is a metachat app — initially in the form of a gpt — that turns the chat thread into an interface into a "socioeconomic media platform" new form of social media.

Indeed, Choir Chat is the world's first AI native social media platform.

The primary objective motivating the development of Choir is the need for a new form of social discourse, one that is intelligent, civil, and inclusive of the broad range of perspectives that comprise humanity.

Current social media platforms fail in that most users consume the content that a small minority creates.

Chat apps — and ChatGPT as a special case — show that all people have something to say. It's just that on social media as we know it, most people don't have good incentives for posting.

The way that social algorithms work, most content created by most users gets minimal attention. And given the way that society processes social media, one would rather have an empty social profile than post a lot but have low follower count.

Really, the downside of posting something that sends the wrong impression — everything offends someone these days, it seems — outweighs the upside of posting, in most cases.

The solution to the problem of oversensitivity and self censorship is of course anonymity, a solution that brings its own problems. Anonymity means sometimes people feel licensed to express their worst qualities, and you get eg 4chan.

For this reason, Choir is built as a gpt, leveraging chatgpt's content moderation. If anything, this means the content may be too tame.

## Socioeconomic media

But removing disincentives for posting with anonymity is not enough. Users need positive incentives to post their thoughts with the internet public.

The people who do post often on social media get social, financial, and political value for the time and energy they expend creating content.

However, most people aren't in a position where the value they get from social media outweighs the cost.

With Choir, all users get value for the time and energy they contribute.

A complex content ecosystem, Choir has 3 different incentive systems that together create an environment which encourages and rewards contributing novel ideas before they beocome widely considered to be important.

In essence, Choir incentivizes people to compete to cooperate to create quality content about complex concepts.

### NOVELTY REWARD

Each message you post with Choir, your message gets compared with all other messages in the Choir database, and the more different the content is from all existing content, the greater your reward in VOICE

### QUOTATION REWARD

Each message Choir receives gets compared to all other messages in the Choir database, and the most valualbe, relevant, similar messages get quoted to you by the choir gpt
The authors of all quoted messages get rewarded VOICE

### CURATION MARKET

When you come across a message that you value, you can invest some of your VOICE in it, increasing its probability of getting quoted to other users, and rewarding its author and prior curators.
Essentially, curation is paying to get more attention on the message and simultaneously betting that it will get curated by others in the future.
When you curate, you may optionally add a message to send to the author and prior curators.
In effect, curators of a message form a private group chat with its author


These 3 incentivized interactions are conducted within the choir gpt,

To use choir gpt, you must be logged into an account on choir.chat. If you are not currently logged in, you will be directed from within chatgpt to register or login to your account.

## Choir.chat

Choir.chat allows signed-in users to view, search, curate, edit, and delete (from choir, not from chatgpt) their own messages, as well as view, search, and curate other user's messages.

There needs to be an account dashboard component search component, a list_of_messages component, a message component, and a curate_message component

account dashboard:

- VOICE balance
- unread messages count
- curated messages count
- quoted by messages count
- authored messages count
- more stats derived from these tbd


message lists:

- unread messages
    - unread messages that quote one of my messages
    - unread messages from cocurators of messages ive curated
- user's messages
    - user-authored messages
    - user-curated messages
- conversations
    - messages that quote one of my messages
    - messages from cocurators of messagesi ive curated
- all messages

sort orders:
- recency
- VOICE
- curator count
- quotation count


message component displays message content and metadata

- content
- metadata
    - created_at_time
    - VOICE_TOTAL = VOICE_INVESTED + VOICE_REWARDED
        - dict of curator_id: VOICE_INVESTED
        - dict of messages that quote it: VOICE_REWARDED
- author_id is not returned by api or displayed to users

curate_message component has parameters for amount of VOICE to invest, optional message text
