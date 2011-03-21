
hsgf = "(;FF[4]EV[hex.mc.2011.feb.1.10]PB[Tiziano]PW[sleepywind]SZ[13]GC[ game #1301977]SO[http://www.littlegolem.com];W[ll];B[swap];W[gg];B[fi];W[ih];B[gd];W[id];B[hj];W[ji])";

// define an eventhandler which is called as parser steps via input string
// header tags needed: FF, SZ

// lexer (syntactic) and parser (semantic)
// 
// lexer is FA

LexState = {
  COLLECTION: "collection",
  GAME : "game",
  SEQ: "seq",
  NODE: "node",
  SUBTREE: "subtree",
  PROP: "prop",
}

// list of transition rules (state + char -> new state + handler name)


function sgfParse(input, handler) {
  var isFirstNode = true;
  var depth = 0;
  var propName = "";
  var accum = "";
  var state = LexState.COLLECTION; 

  for (var i = 0; i < input.length; i++)
  {
    var c = input[i];
    // console.log("state {0} accum {1} char {2}".format(state, accum, c));

    if (state == LexState.COLLECTION && c == "(") {
      state = LexState.SEQ;
      continue;
    }

    if (state == LexState.SEQ && c == ";") {
      state = LexState.NODE;
      continue;
    }

    if (state == LexState.NODE && c == ";") {
      state = LexState.NODE;
      isFirstNode = false;
      continue;
    }

    if (state == LexState.NODE && c == "[") {
      propName = accum;
      accum = "";
      state = LexState.PROP;
      continue;
    }

    if ((state == LexState.SEQ || state == LexState.NODE) && c == "(") {
      accum = "";
      depth++;
      state = LexState.SEQ;
      isFirstNode = false;
      handler.onBranchStart();
      continue;
    }

    if (state == LexState.NODE && c == ")") {
      accum = "";
      if (!depth) {
        // only parses the first game in the tree
        return;
      }

      handler.onBranchStop();
      depth--;
      state = LexState.SEQ;
      continue;
    }

    if (state == LexState.PROP && c == "]") {
      propValue = accum;
      accum = "";
      state = LexState.NODE;

      if (isFirstNode) {
        handler.onGameProperty(propName, propValue);
        continue;
      }

      handler.onMove(propName, propValue);
      continue;
    }

    accum += c;
  }
}

