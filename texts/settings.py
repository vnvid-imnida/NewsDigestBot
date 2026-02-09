SETTINGS_MESSAGE = """
🔧 *Step-by-Step Topics Setup*\n
You can add up to 10 topics.
━━━━━━━━━━━━━━━━━━━━\n
📌 *How it works:*
1. Press 'Enter Topic X'
2. Type your interest
3. Topic saved → next topic
4. Repeat or press 'Stop'\n
👉 *Press button to add first topic:*
"""

ASK_CURRENT_STEP_TOPIC_MESSAGE = (('📝 *Topic {current_step} out of 10*\n\n' +
                                  'Please type your interest:\n') +
                                  '(Be specific for better results)')
MAXIMUM_REACHED_MESSAGE = '🎉 *Maximum reached!* No more topics can be added.'
NEXT_TOPIC_MESSAGE = '*What\'s next?*'
PROCESS_TOPIC_MESSAGE = ('✅ *Topic {topics_count} added:* {topic}\n\n' +
                         '📋 *Your topics ({topics_count}/10):*\n' +
                         '{topics_list}\n\n' +
                         '{status_text}')
SUCCESS_SAVE_MESSAGE = ('✅ *Topics Saved Successfully!*\n\n' +
                        '*Your interests:*\n' +
                        '{formatted_list}\n\n' +
                        'Now use /digest to get news!\n' +
                        'Change anytime with /settings')
CANCEL_SAVE_MESSAGE = 'Topics not saved. Use /settings to start over.'

# Buttons text
ENTER_TOPIC = '📝 Enter Topic'
STOP_ENTERING = '🚫 Stop Entering'
FINISH_SAVE = '✅ Finish & Save'
CLEAR_RESTART = '🗑️ Clear All & Restart'
SAVE_TOPICS = '💾 Save These Topics'
EDIT_TOPICS = '✏️ Edit Topics'
CANCEL = '❌ Cancel'

# Error handling
MAX_TOPICS_REACHED_ERROR = ('❌ Maximum 10 topics reached!\n' +
                            'You cannot add more topics.')
MIN_TOPIC_LENGTH_ERROR = ('❌ Topic too short. Please enter at least 2 characters.\n' +
                          'Try again:')
MAX_TOPIC_LENGTH_ERROR = ('❌ Topic too long. Maximum 100 characters.\n' +
                          'Try again:')
NO_TOPICS_TO_SAVE_ERROR = 'No topics to save. Use /settings to start over.'
PREVIEW_MESSAGE = ('📋 *Final Preview*\n\n' +
                   '*Your topics ({topics_number}/10):*\n' +
                   '{topics_list}\n\n' +
                   '*Save these topics?*')

# Log
LOG_USER_TOPICS = 'User {username} saved topics: {user_topics}'
