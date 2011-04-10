BOARD_SIZE = 13
FIELD_FIRST = {x: 52, y:52}
FIELD_X_DIFF = 25;
FIELD_Y_DIFF = 21;
FIELD_RADIUS = 10;

String.prototype.format = function() {
  var s = this;
  for (var i = 0; i < arguments.length; i++) {
    var reg = new RegExp("\\{" + i + "\\}", "gm");
    s = s.replace(reg, arguments[i]);
  }

  return s;
}

_sgfParseHandler = {
  onGameProperty: sgfOnGameProperty,
  onMove: sgfOnMove,
  onBranchStart: sgfOnBranchStart,
  onBranchStop: sgfOnBranchStop
}

Color = {
  RED: "red",
  BLUE: "blue"
}

MoveType = {
  NORMAL: "normal",
  ROOT: "root",
  SWAP: "swap",
  RESIGN: "resign"
}

STONE_IMG = {red: "/static/img/red_small.gif", blue: "/static/img/blue_small.gif"}
LAST_IMG  = "/static/img/last.gif"

function flipColor(color) {
  if (color == Color.RED)
    return Color.BLUE;
  return Color.RED;
}

// singleton
_gameCreated = false;
function CreateGame() {
  if (_gameCreated)
    return null;
  _gameCreated = true;

  root = new Node(0, 0, 0, null, MoveType.ROOT)
  trunk = {fatherBranch: null, firstNode: root, bid: 0, depth: 0};
  root.branch = trunk;

  game = {
    root: root,
    currNode: root,   
    nodeMap: {0: root},
  };

  game.getColorToMove = function() {
    if (game.currNode.fatherNode == null)
      return Color.RED;
    return flipColor(game.currNode.color);
  };
  return game;
}

// root will be created first
_nextNodeId = 0;

game = CreateGame();

_alphabet = ("abcdefghijklmnopqrstuvwxyz").split("");
function Node(x, y, color, fatherNode, moveType) {
  var that = this
  this.x = x;
  this.y = y;
  this.color = color;
  this.fatherNode = fatherNode;
  this.id = _nextNodeId++;
  this.children = [];
  this.moveType = moveType; 

  if (fatherNode)
    this.number = fatherNode.number + 1;
  else
    this.number = 0;

  this.getAncestors = function() {
    var anc = [];
    var iterNode = that;
    while (iterNode != null) {
      anc[anc.length] = iterNode.id;
      iterNode = iterNode.fatherNode;
    }
    return anc.reverse();
  }

  this.getViewLabel = function() {
    if (that.moveType == MoveType.SWAP)
      return "{0}.swap".format(that.number);
    if (that.moveType == MoveType.ROOT)
      return "root".format(that.number);
    return "{0}.{1}{2}".format(that.number, _alphabet[that.x], that.y + 1);
  }

  this.getChildIndex = function(node) {
    for (var i = 0; i < that.children.length; i++)
      if (that.children[i].id == node.id)
        return i;
    return -1;
  }
  
  this.isBranchRepresentative = function() {
    return that.branch.firstNode.id == that.id;
  }

  return this;
}

_nextBranchId = 1;
function Branch(fatherBranch, firstNode) {
  this.fatherBranch = fatherBranch;
  this.firstNode = firstNode;
  this.bid = _nextBranchId++;
  this.depth = this.fatherBranch.depth + 1;
}

// document events

_sgfStr = "(;FF[4]EV[hex.mc.2011.feb.1.10]PB[Tiziano]PW[sleepywind]SZ[13]GC[ game #1301977]SO[http://www.littlegolem.com];W[ll];B[swap];W[gg];B[fi];W[ih];B[gd];W[id];B[hj];W[ji])";

$(document).ready(function() {
  setupEmptyFields();
  putBranchInTree(game.root.branch);
  putNodeInTree(game.root);

  // give st. to play with
  
  if (_inputSgf.length) {
    sgfParse(_inputSgf, _sgfParseHandler);
  }
  else {
    for (var i = 0; i < 5; i ++) {
      var x = Math.floor(Math.random() * (BOARD_SIZE - 1)); 
      var y = Math.floor(Math.random() * (BOARD_SIZE - 1)); 
      playMove(x, y, game.getColorToMove(), MoveType.NORMAL);
    }
  }
});

$(document).keydown(function(e) {
  switch (e.which) {
    // left
    case 37: 
      if (game.currNode.fatherNode)
        jumpToNode(game.currNode.fatherNode);
      break;
    // right
    case 39: 
      if (game.currNode.children.length)
        jumpToNode(game.currNode.children[0]);
      break;
    // up
    case 38: 
      var up = true;
      cycleBranches(game.currNode, up);
      break;
    // down
    case 40: 
      var up = false;
      cycleBranches(game.currNode, up);
      break;
    // rm sub tree
    case 46: 
      removeSubTree(game.currNode);
      break;
    default: 
      // console.log("pressed {0}".format(e.which));
      break;
  }
});

function setupEmptyFields() {
  for (i = 0; i < BOARD_SIZE * BOARD_SIZE; i++) {
    var coord = {};
    coord.x = i % BOARD_SIZE;
    coord.y = Math.floor(i / BOARD_SIZE);
    setupEmptyField(coord);
  }
}

// this produces position with center of the field (i.e. for empty field)
function coordToPosCenter(coord) {
  var x = FIELD_FIRST.x + coord.x * FIELD_X_DIFF + 0.5 * coord.y * FIELD_X_DIFF;
  var y = FIELD_FIRST.y + coord.y * FIELD_Y_DIFF;
  return {x:x, y:y};
}

// this produces position with top left of the field (i.e. for a stone pic)
function coordToPosTopLeft(coord) {
  var pos = coordToPosCenter(coord);
  pos.x -= FIELD_RADIUS + 4;
  pos.y -= FIELD_RADIUS + 3;
  return pos;
}

function setupEmptyField(coord) {
  var pos = coordToPosCenter(coord);
  var elem = $('<area id="empty_field_' + coord.x + '_' + coord.y + '" href="" coords="' + pos.x + ',' + pos.y + ',' + FIELD_RADIUS + '" shape="circle"/>')
  elem.appendTo("#empty_fields");
  elem.click(function(e) {
      e.preventDefault();
      playMove(coord.x, coord.y, game.getColorToMove(), MoveType.NORMAL);
  });
}

function playMove(x, y, color, moveType) {
  var existingNode = false; 
  // just continues in current branches
  game.currNode.children.forEach( function(child) {
    if (child.x == x && child.y == y && child.color == color) {
      game.currNode = child;
      putNodeOnBoard(game.currNode);
      setNodeActive(game.currNode, true);
      existingNode = true;
    }
  });
  if (existingNode)
    return;

  // console.log("playing new move father id {0}".format(game.currNode.id));

  var newNode = new Node(x, y, color, game.currNode, moveType);
  var branch
  if (!game.currNode.children.length)
    branch = game.currNode.branch;
  else {
    branch = new Branch(game.currNode.branch, newNode);
    putBranchInTree(branch);
  }

  newNode.branch = branch;
  game.currNode.children[game.currNode.children.length] = newNode;
  game.nodeMap[newNode.id] = newNode;
  game.currNode = newNode;

  putNodeInTree(game.currNode);
  putNodeOnBoard(game.currNode);
}

function putBranchInTree(branch) {
  var elemStr = "<div id='branch_{0}' class='branch' style='margin-left: {1}px;'></div>";
  var elem = $(elemStr.format(branch.bid, 15 * branch.depth));
  if (branch.depth)
    elem.append("");
  $("#branches").append(elem);
}

function removeBranchFromTree(branch) {
  var elem = $("#branch_{0}".format(branch.bid));
  elem.remove();
}

function removeNodeFromTree(node) {
  var elem = $("#node_{0}".format(node.id));
  elem.remove();
}

function putNodeInTree(node) {
  var elemStr = "<a href='' class='node_link active' id='node_{0}'>{1}</a>"
  var elem = $(elemStr.format(node.id, node.getViewLabel()))
  // not all nodes have color (i.e. start node)
  if (node.color)
    elem.addClass(node.color == Color.RED ? "red" : "blue");
  //if (node.children.length > 1)
    //elem.addClass("junction");
  $("#branch_" + node.branch.bid).append(elem).append(" ");
  elem.click(function(e) {
      e.preventDefault();
      jumpToNode(node);
  });
}

function setNodeActive(node, active) {
  var elem = $("#node_" + node.id);
  if (active)
    elem.addClass("active");
  else
    elem.removeClass("active");
}

function putNodeOnBoard(node) {
  if (node.moveType == MoveType.SWAP) {
    removeNodeFromBoard(node.fatherNode);
    putNodeOnBoardNoSwap(node);
  }
  else 
    putNodeOnBoardNoSwap(node);
}


function putLastMoveMark(x, y) {
  // update last mark
  var last = $("#last_stone") 
  if(!last.length) {
    last = $("<img alt='' style='z-index: 1; position: absolute; left: " + x + "px ; top : " + y + "px ;' galleryimg='no' id='last_stone' src='" + LAST_IMG + "'>");
    last.appendTo("#board");
  }
  var pos = coordToPosTopLeft({x:x, y:y});
  last.css("left", pos.x);
  last.css("top", pos.y);
  last.show();
}

function removeLastMoveMark() {
  last = $("#last_stone") 
  if(last)
    last.hide();
}

function putNodeOnBoardNoSwap(node) {
  // remove empty field on that location
  elem = $("#empty_field_" + node.x + "_" + node.y)
  elem.remove();

  // add new empty field
  var pos = coordToPosTopLeft({x:node.x, y:node.y});
  var imgLocation = node.color == Color.RED ? STONE_IMG.red : STONE_IMG.blue;
  elem = $("<img alt='' class='move' style='position: absolute; left: " + pos.x + "px ; top : " + pos.y + "px ;' galleryimg='no' id='move_" + node.x + "_" + node.y + "' src='" + imgLocation + "'>");
  elem.appendTo("#board");

  elem.click(function(e) {
    e.preventDefault();
    jumpToNode(node);
  });

  putLastMoveMark(node.x, node.y);
}

function removeNodeFromBoard(node) {
  removeMoveFromBoard(node.x, node.y);
  // with swap add nodes father
  if (node.moveType == MoveType.SWAP)
    putNodeOnBoard(node.fatherNode);
}

function removeMoveFromBoard(x, y) {
  // remove move
  elem = $("#move_" + x + "_" + y);
  elem.remove();
  setupEmptyField({x:x, y:y});
}

function removeNode(node) {
  // shouldn't happen
  if (!node.fatherNode)
    return;

  node.children.forEach(function(child) {
    removeNode(child);
    });

  if (node.isBranchRepresentative()) {
    removeBranchFromTree(node.branch);
    delete node.branch;
  }

  removeNodeFromTree(node);
  delete game.nodeMap[node.id];
  delete node;
}

function removeSubTree(node) {
  father = node.fatherNode;
  if (!father)
    return;

  branch = node.branch;
  jumpToNode(father);
  removeNode(node);

  // remove node from father children array
  var i = father.getChildIndex(node);  
  father.children.splice(i, 1);

  // promote first children variant
  if (i == 0 && father.children.length > 0)
  {
    removeBranchFromTree(father.children[0].branch);
    promoteToNewBranch(father.children[0], father.branch)
  }
}

function promoteToNewBranch(node, newBranch) {
  while (true) {
    node.branch = newBranch;
    putNodeInTree(node);
    setNodeActive(node, false);

    if (!node.children.length)
      break;
    node = node.children[0];
  }
}

function cycleBranches(node, up) {
  if (!node.fatherNode)
    return;

  var father = node.fatherNode; 
  var i = node.fatherNode.getChildIndex(node);  
  if (i == -1) 
    return;

  if (up && i > 0)
    jumpToNode(father.children[i - 1]);

  if (!up && i < father.children.length - 1)
    jumpToNode(father.children[i + 1]);
}

function jumpToNode(newNode) {
  if (game.currNode.id == newNode.id)
    return;
  //var newNode = game.nodeMap[id]
  //if (!newNode)
    //return;

  // get id of closest common junction
  ancNew = newNode.getAncestors();
  ancOld = game.currNode.getAncestors();

  var i
  for (i = 0; i < Math.min(ancNew.length, ancOld.length); i++)
    if (ancNew[i] != ancOld[i])
      break;

  var ancCommon = game.nodeMap[ancNew[i - 1]];

  // console.log("curr node id {0}".format(game.currNode.id));
  // console.log("anc new {0} anc old {1}".format(ancNew, ancOld));
  // console.log("new {0} old {1} common {2}".format(newNode.id, game.currNode.id, ancCommon.id));

  // backwards currNode -> common
  var node = game.currNode
  while (node.id != ancCommon.id) {
    setNodeActive(node, false);
    removeNodeFromBoard(node);
    node = node.fatherNode;
  }

  // backwards newNode -> common
  var node = newNode
  while (node.id != ancCommon.id) {
    setNodeActive(node, true);
    putNodeOnBoard(node);
    node = node.fatherNode;
  }
  if(newNode.fatherNode)
    putLastMoveMark(newNode.x, newNode.y);
  else
    removeLastMoveMark(newNode.x, newNode.y);

  game.currNode = newNode;
}

// sgf parsing

function sgfOnGameProperty(propName, propValue) {
  // console.log("sgf on game property name {0} value {1}".format(propName, propValue));
  if (propName == "FF" && propValue != "4")
    throw "invalid game type";
  if (propName == "SZ" && propValue != "13")
    throw "invalid board size";
  // player names
  if (propName == "PB")
    $("#red_player").text(propValue);
  if (propName == "PW")
    $("#blue_player").text(propValue);
}

function sgfOnMove(who, where) {
  // console.log("sgf on move who {0} where {1}".format(who, where));
  color = who == "W" ? Color.RED : Color.BLUE;
  if (who != "W" && who != "B")
    throw "invalid move color {0}".format(who)

  if (where == "swap")
  {
    playMove(game.currNode.y, game.currNode.x, color, MoveType.SWAP);
    return;
  }

  if (where.length > 2)
    throw "invalid move definition length {0}".format(where)

  var x = _alphabet.indexOf(where[0]);
  var y = _alphabet.indexOf(where[1]);
  if (x == -1 || y == -1)
    throw "invalid move definition {0}".format(where)

  playMove(x, y, color, MoveType.NORMAL);
}

function sgfOnBranchStart() {
  throw "not implemented";
}

function sgfOnBranchStop() {
  throw "not implemented";
}

