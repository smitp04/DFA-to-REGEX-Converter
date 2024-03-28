import streamlit as st
# CONVERT DFA TO REGEX
import graphviz as gv
import json
import sys

def join(string1, string2):
    if string1 == '$':
        return string2
    if string2 == '$':
        return string1
    return string1 + string2


# remove dead states

def resolve_dead(delta, DFA):
    check = {}
    for state in DFA['states']:
        check.update({state: False})
    for state in DFA['start_states']:
        check[state] = True
    for edge in delta:
        check[edge[2]] = True
    return [edge for edge in delta if check[edge[0]]], [state for state in check if check[state]]


# simplifty parallel edges

def resolve_parallel(delta):
    hist = []
    n = len(delta)
    for i in range(n):
        for j in range(i+1, n):
            if delta[i][0] == delta[j][0] and delta[i][2] == delta[j][2]:
                new_edge = [
                    delta[i][0], '(' + delta[i][1] + '+' + delta[j][1] + ')', delta[i][2]]
                delta.remove(delta[j])
                delta.append(new_edge)
                hist.append(delta[i])
                i += 1
    for old_edge in hist:
        if old_edge in delta:
            delta.remove(old_edge)
    return delta


# removing self-loops

def resolve_selfloops(delta):
    loops = []
    for edge in delta[:]:
        if edge[0] == edge[2]:
            loops.append(edge)
            delta.remove(edge)
    for loop in loops:
        for i, edge in enumerate(delta):
            if loop[0] == edge[0]:
                delta[i][1] = join('(' + loop[1] + ')*', edge[1])
    return delta


def remove_state(state, delta):
    incoming = [edge for edge in delta if edge[2] == state]
    outgoing = [edge for edge in delta if edge[0] == state]
    for edge in (incoming + outgoing):
        delta.remove(edge)
    for inedge in incoming:
        for outedge in outgoing:
            edge = [inedge[0], join(inedge[1], outedge[1]), outedge[2]]
            delta.append(edge)
    delta = resolve_parallel(delta)
    delta = resolve_selfloops(delta)
    return delta


def dfatoregex(DFA):
    delta = DFA['transition_function'].copy()

    # STEP ZERO: remove dead states

    delta, valid_states = resolve_dead(delta, DFA)

    # STEP ONE: NEW INITIAL AND FINAL STATES

    start = 'Qs'
    final = 'Qf'

    for s in DFA['start_states']:
        delta.append([start, '$', s])
    for f in DFA['final_states']:
        delta.append([f, '$', final])

    # STEP TWO: simplify parallel edges

    delta = resolve_parallel(delta)

    # STEP THREE: removing self-loops

    delta = resolve_selfloops(delta)

    for state in valid_states:
        delta = remove_state(state, delta)

    # regex = {'regex': delta[0][1]}
    # output = json.dumps(regex, indent=4)
    return delta[0][1]

def visualize_finite_automata(data):
    states = data['states']
    letters = data['letters']
    transitions = data['transition_function']
    start_states = data['start_states']
    final_states = data['final_states']

    # Convert final state 2D list to comma-separated string
    for i, state in enumerate(final_states):
        if isinstance(state, list):
            final_states[i] = ",".join(state)
            
    # Rename 2D array of states as 1 state
    for i, state in enumerate(states):
        if isinstance(state, list):
            states[i] = ",".join(state)

    # Rename 2D array of states as 1 state in transition_function
    for i, transition in enumerate(transitions):
        if isinstance(transition[0], list):
            transitions[i][0] = ",".join(transition[0])
        if isinstance(transition[2], list):
            transitions[i][2] = ",".join(transition[2])

    # Initialize the graph
    graph = gv.Digraph(format='svg')
    graph.attr(rankdir='LR')

    # Add nodes
    for state in states:
        if state in final_states:
            graph.node(state, shape='doublecircle')
        else:
            graph.node(state)

    # Add edges
    for transition in transitions:
        start_state, letter, end_state = transition
        if letter == "$":
            graph.edge(start_state, end_state, label="ε")
        else:
            graph.edge(start_state, end_state, label=letter)

    # Return the graph object
    return graph

# Set the page width to a high value
st.set_page_config(page_title="DFA to REGEX Converter", layout="wide", initial_sidebar_state="collapsed")

# Streamlit app
st.title("DFA to REGEX Converter")

with st.sidebar:
    st.header("Input")
    file1 = st.file_uploader("Upload JSON file for Given DFA", type=["json"])

if file1 is not None:
    # Load JSON data
    data1 = json.load(file1)
    regex_pattern=dfatoregex(data1)

    # Display the finite automata diagrams side by side
    col1, col2 = st.columns(2)

    # Create the graphs
    graph1 = visualize_finite_automata(data1)

    # Display the graphs in the columns
    with col1:
        st.header("Input (DFA)")
        st.graphviz_chart(graph1, use_container_width=True)
    with col2:
        st.header("Output (REGEX of Given DFA)")
        # regex_pattern = "(1((0+1))**+00((0+1))**)"
        escaped_pattern = regex_pattern.replace("*", "<sup>&#42;</sup>")
        st.markdown(f"<code style='background-color: white; font-size: 20px'>{escaped_pattern}</code>", unsafe_allow_html=True)

