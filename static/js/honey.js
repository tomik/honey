BOARD_SIZE = 13
FIELD_FIRST = {x: 52, y:52}
FIELD_X_DIFF = 25;
FIELD_Y_DIFF = 21;
FIELD_RADIUS = 10;

/*
 * TODO
 * highlight last move
 * hide/show branches
 */

String.prototype.format = function() {
  var s = this;
  for (var i = 0; i < arguments.length; i++) {
    var reg = new RegExp("\\{" + i + "\\}", "gm");
    s = s.replace(reg, arguments[i]);
  }

  return s;
}

Color = {
  RED: "red",
  BLUE: "blue"
}

STONE_IMG = {red: "/static/img/red.gif", blue: "/static/img/blue.gif"}

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

  root = {fatherNode: null, children: [], id: 0, number: 0};
  trunk = {fatherBranch: null, firstNode: root, bid: 0, depth: 0};
  root.branch = trunk;
  root.getAncestors = function() {return [0];}
  root.getViewLabel = function() {return "root"};

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

game = CreateGame();

_nextNodeId = 1;
_alphabet = ("abcdefghipqrstuvwxyz").split("");
function Node(x, y, color, fatherNode) {
  var that = this
  this.x = x;
  this.y = y;
  this.color = color;
  this.fatherNode = fatherNode;
  this.id = _nextNodeId++;
  this.number = fatherNode.number + 1;
  this.children = [];

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

$(document).ready(function() {
  setupEmptyFields();
  putBranchInTree(game.root.branch);
  putNodeInTree(game.root);

  // give st. to play with
  for (var i = 0; i < 5; i ++) {
    var x = Math.floor(Math.random() * (BOARD_SIZE - 1)); 
    var y = Math.floor(Math.random() * (BOARD_SIZE - 1)); 
    playMove(x, y, game.getColorToMove());
  }
});

$(document).keydown(function(e) {
  switch (e.which) {
    // left
    case 37: 
      console.log(game.currNode);
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
      console.log("pressed {0}".format(e.which));
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
      playMove(coord.x, coord.y, game.getColorToMove());
  });
}

function playMove(x, y, color) {
  var existingNode = false; 
  // just continues in current branches
  game.currNode.children.forEach( function(child) {
    if (child.x == x && child.y == y && child.color == color) {
      game.currNode = child;
      putMoveOnBoard(x, y, game.currNode.color);
      // TODO switch to branch
      existingNode = true;
    }
  });
  if (existingNode)
    return;

  // console.log("playing new move father id {0}".format(game.currNode.id));

  var newNode = new Node(x, y, color, game.currNode);
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
  putMoveOnBoard(x, y, game.currNode.color);
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

function putMoveOnBoard(x, y, color) {
  // remove empty field on that location
  elem = $("#empty_field_" + x + "_" + y)
  elem.remove();

  // add new empty field
  var pos = coordToPosTopLeft({x:x, y:y});
  var imgLocation = color == Color.RED ? STONE_IMG.red : STONE_IMG.blue;
  elem = $("<img alt='' class='move' style='position: absolute; left: " + pos.x + "px ; top : " + pos.y + "px ;' galleryimg='no' id='move_" + x + "_" + y + "' src='" + imgLocation + "'>");
  elem.appendTo("#board");
}

function removeMoveFromBoard(x, y, color) {
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
  if (!node.fatherNode)
    return;

  jumpToNode(node.fatherNode);
  removeNode(node);

  // remove node from father children array
  var i = node.fatherNode.getChildIndex(node);  
  node.fatherNode.children.splice(i, 1);
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
    removeMoveFromBoard(node.x, node.y);
    node = node.fatherNode;
  }

  // backwards newNode -> common
  var node = newNode
  while (node.id != ancCommon.id) {
    setNodeActive(node, true);
    putMoveOnBoard(node.x, node.y, node.color);
    node = node.fatherNode;
  }

  game.currNode = newNode;
}

// FORMAT:
// r1-1 swap r7-7 b1-2 ((r4-3 b6-5) (r3-2)) (r5-1)

