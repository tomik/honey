
# Handles interaction between html and game clientside js logic.
# Takes care of passing input values (e.g. sgf) and retrieving outputs (e.g. current node changed).

class Bridge
  constructor: (@inputSgf, @currNodeChangeHandler) ->
  getCurrNodePath: () ->
    # Returns path to current node in json format as [(branch, node), ...].
    # Example:
    # [(0, 7), (1, 3)] means:
    # Move on 7th node in the main branch, then move to the 3rd node on the first branch
    # this function is overriden by game clientside logic
    throw "NotImplemented"
  onCurrNodeChange: () ->
    @currNodeChangeHandler()


@Bridge = Bridge

