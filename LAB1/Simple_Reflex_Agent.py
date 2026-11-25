
def simple_reflex_agent(percept):

    if percept == "dirty":
        return "Clean the room"

    elif percept == "clean":
        return "Move to next room"

    else:
        return "Invalid percept"


# Input
percept = input("Enter room status (dirty/clean): ")

# Output
action = simple_reflex_agent(percept)

print("Agent Action:", action)
