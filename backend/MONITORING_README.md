# Conversation Monitoring System

This system provides comprehensive real-time monitoring of conversations between users and the LiveKit AI agent. All conversation data is logged to the terminal with detailed formatting and timestamps.

## Features

🎤 **Real-time Transcription Monitoring**
- Partial transcripts (real-time speech recognition)
- Final transcripts (committed user messages)

💬 **Complete Conversation History**
- User messages with timestamps
- Agent responses with timestamps
- System messages
- Interruption detection

🤖 **Agent State Tracking**
- Initializing → Listening → Thinking → Speaking
- Visual state transition indicators

👤 **User State Tracking**
- Speaking ↔ Listening transitions
- Voice Activity Detection (VAD) events

🔧 **Function Tool Monitoring**
- Function calls with parameters
- Function results
- Execution timing

⚙️ **Business Logic Events**
- Custom event logging
- Error handling
- Session lifecycle management

## Installation

The monitoring system is automatically integrated into your LiveKit agent. No additional setup required!

## Usage

### Automatic Monitoring

When you run your LiveKit agent, conversation monitoring starts automatically:

```bash
cd backend
python agent.py
```

### Monitor Output Example

```
================================================================================
🎤 CONVERSATION MONITOR STARTED
================================================================================
🚀 SESSION STARTED - Room: room-abc123

🔄 AGENT STATE: 🔧 initializing → 👂 listening
🔄 USER STATE: 👂 listening → 🎤 speaking

📝 PARTIAL: Hello
📝 PARTIAL: Hello, I need
📝 PARTIAL: Hello, I need help
🎯 FINAL TRANSCRIPT: Hello, I need help with my car

--------------------------------------------------------------------------------
👤 USER MESSAGE #1
💬 Hello, I need help with my car

🔄 AGENT STATE: 👂 listening → 🤔 thinking
ℹ️  No car found, initiating VIN lookup for: Hello, I need help with my car

🔧 FUNCTION TOOLS EXECUTED:
   🛠️  Function: lookup_car
   📥 Args: {"vin": "1HGBH41JXMN109186"}
   📤 Result: Car not found

🔄 AGENT STATE: 🤔 thinking → 🗣️ speaking
🗣️  AGENT SPEECH CREATED - Source: generate_reply

--------------------------------------------------------------------------------
🤖 AGENT RESPONSE #2
💬 I'd be happy to help! I couldn't find that VIN. Could you provide your car's make, model, and year?

🔄 AGENT STATE: 🗣️ speaking → 👂 listening
```

### Configuration Options

You can customize the monitoring behavior by modifying the ConversationMonitor initialization:

```python
# Enable/disable partial transcripts
monitor = ConversationMonitor(session, enable_partial_transcripts=True)

# Log custom events
monitor.log_custom_event("User provided VIN successfully")
monitor.log_custom_event("Database connection failed", level="error")
```

## Log Levels and Icons

### Message Types
- 👤 **User Messages**: Direct user input
- 🤖 **Agent Responses**: AI-generated responses
- ⚙️ **System Messages**: Internal system communications

### State Changes
- 🔧 **Initializing**: Agent starting up
- 👂 **Listening**: Waiting for user input
- 🤔 **Thinking**: Processing user input
- 🗣️ **Speaking**: Agent generating/playing response
- 🎤 **User Speaking**: User is talking
- 👂 **User Listening**: User stopped talking

### Function Tools
- 🔧 **Function Execution**: Tool/function being called
- 🛠️ **Function Name**: Specific function being executed
- 📥 **Function Args**: Input parameters
- 📤 **Function Result**: Output/return value

### Transcription
- 📝 **Partial Transcript**: Real-time speech recognition (incomplete)
- 🎯 **Final Transcript**: Completed transcription
- ⚠️ **Interrupted**: Message was cut off

### Events
- 🚀 **Session Start**: Conversation session begins
- 🏁 **Session End**: Conversation session ends
- ℹ️ **Info**: General information
- ⚠️ **Warning**: Non-critical issues
- ❌ **Error**: Critical problems

## File Structure

```
backend/
├── agent.py                 # Main agent with monitoring integrated
├── conversation_monitor.py  # Core monitoring functionality
├── test_monitoring.py       # Demo script
├── api.py                   # Enhanced with monitoring logs
└── requirements.txt         # Dependencies
```

## Testing the Monitor

Run the demo script to see what the monitoring output looks like:

```bash
cd backend
python test_monitoring.py
```

This will show you a simulated conversation with all the monitoring features in action.

## Integration Details

The monitoring system hooks into LiveKit agent events:

- `conversation_item_added`: Captures committed conversation items
- `user_input_transcribed`: Real-time transcription updates
- `speech_created`: Agent speech generation events
- `agent_state_changed`: Agent state transitions
- `user_state_changed`: User state transitions
- `function_tools_executed`: Function/tool execution
- `close`: Session end events

## Customization

### Adding Custom Events

```python
# In your agent code
monitor.log_custom_event("VIN lookup successful")
monitor.log_custom_event("Database timeout", level="warning")
monitor.log_custom_event("Critical system failure", level="error")
```

### Disabling Partial Transcripts

```python
# If you only want final transcripts
monitor = ConversationMonitor(session, enable_partial_transcripts=False)
```

### Getting Statistics

```python
stats = monitor.get_conversation_stats()
print(f"Total conversation items: {stats['total_conversation_items']}")
```

## Troubleshooting

### No Monitoring Output
- Ensure `conversation_monitor.py` is in the same directory as `agent.py`
- Check that the ConversationMonitor is properly initialized
- Verify logging level is set to INFO or lower

### Partial Transcripts Not Showing
- Set `enable_partial_transcripts=True` in ConversationMonitor initialization
- Check STT configuration in your agent

### Function Calls Not Logged
- Ensure your function tools are decorated with `@function_tool`
- Check that functions are properly registered with the agent

## Performance Notes

- Monitoring adds minimal overhead to your agent
- Logs are written to console only (no file I/O)
- All event handlers are non-blocking
- Safe error handling prevents monitoring from affecting agent functionality

## Support

The monitoring system is designed to be:
- **Non-intrusive**: Won't affect your agent's core functionality
- **Robust**: Handles errors gracefully
- **Informative**: Provides comprehensive conversation insights
- **Customizable**: Easy to extend and modify

For issues or feature requests, check the agent logs for any error messages from the conversation monitor.
