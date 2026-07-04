import sys; sys.path.insert(0, '.')
from services.conversation_service import ConversationService
cs = ConversationService.__new__(ConversationService)

tests = [
    ('Open Google', 'Open Google'),
    ('Create Flask API', 'Create Flask API'),
    ('Help me deploy GreenOps', 'Deploy GreenOps'),
    ("What's the weather?", 'Weather'),
    ('Write a Python script to parse CSV files', 'Write a Python script to pa...'),
    ('Can you open Chrome for me?', 'open Chrome'),
    ('Explain quantum computing', 'Explain quantum computing'),
    ('', 'New Conversation'),
    ('   ', 'New Conversation'),
    ('Generate a function to sort an array', 'Generate a function to sort...'),
    ('Tell me how to write unit tests', 'write unit tests'),
    ('What is Python?', 'What is Python'),
]

all_pass = True
for inp, expected in tests:
    result = cs._generate_title(inp)
    status = 'OK' if result == expected else 'FAIL'
    print(f'[{status}] "{inp}" -> "{result}" (expected: "{expected}")')
    if result != expected:
        all_pass = False

print()
print('All passed!' if all_pass else 'Some tests FAILED!')
sys.exit(0 if all_pass else 1)
