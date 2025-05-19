//Applies CSS classes to card elements based on their data-name attribute.
function applyCardCSS() {
    let cards=document.getElementsByClassName("card");

    for (let i=0;i<cards.length;i++) {
        let card=cards[i];
        let cardName=card.getAttribute("data-name");

        if (cardName && cardFinder[cardName]) {
            let cardInfo=cardFinder[cardName];

            card.classList.add(cardInfo.className);
        }
    }
}



//Run only once at match start to make opponent cards initially clickable.
function setInitialCardsAsTargetable(){
	let opponentCards=document.getElementsByClassName("opponent-card");
	for(var i=0;i<opponentCards.length;i++){
		let card=opponentCards[i];
		if (card.getAttribute("data-name")!=="No card") {
			card.classList.add("targetable");
		}
	}
}



//Sets the width of a single card based on its height to maintain aspect ratio.
function setCardAspectRatio(card){
	let height=card.offsetHeight;
	let width=0.714*height;
	card.style.width=width+"px";
}



//Applies aspect ratio calculation to all elements with class "card".
function setCardsAspectRatio(){
	let cards=document.getElementsByClassName("card");
	for(var i=cards.length-1;i>=0;i--){
		setCardAspectRatio(cards[i]);
	}
}



//Toggles the visibility of the chat box container.
function toggleChatBox(){
	let chatBox=document.getElementsByClassName("chat-container")[0];
	let computedStyle=getComputedStyle(chatBox);
	if(computedStyle.display=="none"){
		chatBox.style.display="block";
	}else if(computedStyle.display=="block"){
		chatBox.style.display="none";
	}
}



//Sends a chat message via websocket after basic validation.
function send(){
	let textInput=document.getElementsByClassName("chat-input")[0];
	let text=textInput.value;

	//Prevent empty messages or messages with basic HTML tags.
	if(text==''){
		alert("enter something before sending");
		return;
	}else if(text.includes("<")||text.includes(">")){
		alert("illegal character");
		return;
	}
	let message={
		type:"chat",
		text:text
	};
	if(socket&&socket.readyState===WebSocket.OPEN){
		socket.send(JSON.stringify(message));
		document.getElementsByClassName("chat-input")[0].value="";
	}else{
        alert("WebSocket connection is not open.");
    }
}



//Adds a message string to the chat display area.
function addMessage(text){
	let message=document.createElement("div");
	let chatBox=document.getElementsByClassName("chatbox")[0];
	message.innerHTML=text;
	message.classList.add("message");
	chatBox.append(message);
}


//Removes 'targeted' ID from opponent cards and resets targetedCardIndex.
function clearTargets(){
	let opponentCards=document.getElementsByClassName("opponent-card");
	for(var i=opponentCards.length-1;i>=0;i--){
		opponentCards[i].id="";
	}
	targetedCardIndex=null;
}


//Removes 'active' class from player cards and resets activeCardIndex.
function clearPlayerActiveCards(){
	let playerCards=document.getElementsByClassName("player-card");
	for(var i=playerCards.length-1;i>=0;i--){
		playerCards[i].classList.remove("active");
	}
	activeCardIndex=null;
}


//Removes 'active' class from opponent cards.
function clearOpponentActiveCards(){
	let opponentCards=document.getElementsByClassName("opponent-card");
	for(var i=opponentCards.length-1;i>=0;i--){
		opponentCards[i].classList.remove("active");
	}
}



//Visually marks an opponent card as the target for an ability, if it's the player's turn.
function setTarget(clickedCard,targetNumber){
	//Only allow targeting if it is this player's turn.
	if(nextActioningPlayerUid===uid){
		clearTargets();
		clickedCard.id="targeted";
		//Store the index of the currently targeted card globally.
	    targetedCardIndex=targetNumber;
	}
}



//Sends an ability usage action via websocket after validation.
function useAbility(attackingPlayerUid,attackingCardIndex,abilityNumber,targetedPlayerUid){
	//Prevent action if it's not the player's turn.
    if(attackingPlayerUid!==nextActioningPlayerUid){
        alert("It's not your turn!");
        return;
    }
	//Prevent action if no target card is selected.
    if(targetedCardIndex===null){
    	alert("No target selected");
    	return;
    }
    //Prevent action if card is not active
    if(attackingCardIndex!==activeCardIndex){
    	return;
    }
	//Construct the action message payload.
	let message={
		type:"action",
		attackingPlayerUid:attackingPlayerUid,
		attackingCardIndex:attackingCardIndex,
		targetedPlayerUid:targetedPlayerUid,
		targetedCardIndex:targetedCardIndex, //Uses the globally stored index.
		abilityNumber:abilityNumber,
		activeCardIndex:activeCardIndex
	};
	//Send the action if the connection is active.
	if(socket&&socket.readyState===WebSocket.OPEN){
		socket.send(JSON.stringify(message));
	}else{
        alert("WebSocket connection is not open.");
    }
}



//Displays the card swap
function displaySwap(swapData){
	//Check if the current client's player was the one swapping.
	if(swapData["swapping_player_uid"]===uid){

		//Update the players displayed active card.
		let cards=document.getElementsByClassName("player-card");
		let swapTargetCard=cards[swapData["swap_target_card_index"]]
		swapTargetCard.classList.add("active")
		activeCardIndex=swapData["swap_target_card_index"]

	//Check if the current client's player was the one attacking.
	}else if(swapData["opponent_uid"]===uid){

		//Update the opponents displayed active card.
		clearOpponentActiveCards();
		let cards=document.getElementsByClassName("opponent-card");
		let swapTargetCard=cards[swapData["swap_target_card_index"]]
		swapTargetCard.classList.add("active")

	}
}


//Sends swap action via websocket after validation
function swap(swappingPlayerUid,swapTargetCardIndex,opponentUid){
	//Prevent swap if it's not the player's turn.
    if(swappingPlayerUid!==nextActioningPlayerUid){
        alert("It's not your turn!");
        return;
    }
	//Prevent swap if no swap target card is selected.
    if(swapTargetCardIndex===null){
    	alert("No swap target selected");
    	return;
    }
    //Prevent swapping to active card
    if(swapTargetCardIndex===activeCardIndex){
    	alert("Swap target is already the active card!")
    	return;
    }
    clearPlayerActiveCards();
	//Construct the action message payload.
	let message={
		type:"swap",
		swappingPlayerUid:swappingPlayerUid,
		opponentUid:opponentUid,
		swapTargetCardIndex:swapTargetCardIndex
	};
	//Send the action if the connection is active.
	if(socket&&socket.readyState===WebSocket.OPEN){
		socket.send(JSON.stringify(message));
	}else{
        alert("WebSocket connection is not open.");
    }
}


//Updates the displayed HP of a card after receiving action data from the server.
function setHp(actionData){
	//Check if the current client's player was the one targeted.
	if(actionData["targeted_player_uid"]===uid){

		//Update the targeted player card's HP display.
		let cards=document.getElementsByClassName("player-card");
		let hp=cards[actionData["targeted_card_index"]].getElementsByClassName("hp")[0];
		hp.innerHTML=actionData["target_hp"];

		//Handle card death if HP is zero or less.
		if(actionData["target_hp"]<=0){
			death(cards[actionData["targeted_card_index"]],uid);
		}

	//Check if the current client's player was the one attacking.
	}else if(actionData["attacking_player_uid"]===uid){

		//Update the targeted opponent card's HP display.
		let cards=document.getElementsByClassName("opponent-card");
		let hp=cards[actionData["targeted_card_index"]].getElementsByClassName("hp")[0];
		hp.innerHTML=actionData["target_hp"];

		//Handle card death if HP is zero or less.
		if(actionData["target_hp"]<=0){
			death(cards[actionData["targeted_card_index"]],uid);
		}
	}
}


//Handles visual updates and disables interactions when a card reaches 0 HP.
function death(cardElement,cardOwnerUid){
	cardElement.onclick=null;
	cardElement.classList.add("defeated");
	cardElement.classList.remove("targetable");
	cardElement.classList.remove("targeted");

	//If the defeated card belongs to the current player, remove its ability buttons.
	if(cardOwnerUid===uid){
		let abilityButtons=cardElement.getElementsByClassName("ability");
		for(var i=abilityButtons.length-1;i>=0;i--){
			abilityButtons[i].remove();
		}
	}
}



//Updates the visual turn indicator based on whose turn it is.
function displayTurn(nextActioningPlayerUid){
	turnDisplay=document.getElementsByClassName("turn-display")[0];
	//Ensure no targets linger between turns.
	clearTargets();

	//Set indicator color: green for player's turn, red for opponent's.
	if(nextActioningPlayerUid===uid){
		turnDisplay.style.backgroundColor="green";
	}else{
		turnDisplay.style.backgroundColor="red";
	}
}



//Closes the websocket connection and redirects the user to the homepage.
function exit(){
	if(socket&&socket.readyState===WebSocket.OPEN){
        socket.close();
	}
	redirect();
}


//Redirects the browser to the homepage.
function redirect(){
	window.location.href="/";
}



//Establish WebSocket connection for the match.
let protocol=window.location.protocol==="https:"?"wss://":"ws://";
let wsURL=protocol+location.host+"/chat/match/"+matchID;
let socket=new WebSocket(wsURL);



//Send authentication details once the connection is established.
socket.addEventListener("open",(event)=>{
	let authMessage={
		type:"auth",
		uid:uid
	};
	if(socket.readyState===WebSocket.OPEN){
	    socket.send(JSON.stringify(authMessage));
    }
});



//Handles incoming WebSocket messages from the server.
socket.addEventListener("message",(event)=>{
    //Safely parse incoming JSON data.
    try{
        let receivedMessage=JSON.parse(event.data);

        //Handle server-generated disconnect notification strings.
        if(typeof receivedMessage==="string"&&
            receivedMessage.startsWith("SERVER: ")&&
            receivedMessage.endsWith(" has disconnected, redirecting in 5 seconds...")){
            addMessage(receivedMessage);
        	setTimeout(redirect,5000); //Schedule redirect after delay.

        //Handle regular chat messages (strings).
        }else if(typeof receivedMessage==="string"){
        	addMessage(receivedMessage);

        //Handle game state updates (objects).
        }else if(typeof receivedMessage==="object"){

        	//Process action results (e.g., HP changes).
        	if(receivedMessage["type"]==="action"){
        		setHp(receivedMessage);

        	//Process turn updates.
        	}else if(receivedMessage["type"]==="turn"){
        		if(receivedMessage["losing_player"]===null){
        			nextActioningPlayerUid=receivedMessage["next_actioning_player_uid"];
                	displayTurn(nextActioningPlayerUid);
        		}else if(receivedMessage["losing_player"]===true){
        			setTimeout(redirect,1000);
        			alert(`The match has ended in a tie! Returning to home page after clicking ok on this alert`)
        		}else{
        			losingPlayer=receivedMessage["losing_player"];
        			setTimeout(redirect,1000);
        			alert(`${losingPlayer} has lost! Returning to home page after clicking ok on this alert`)
        		};

            }else if(receivedMessage["type"]==="swap"){
            	displaySwap(receivedMessage);
            }
        }
    //Ignore messages that fail parsing or don't match expected formats.
    }catch(error){}
});


//checks for empty match
function checkForEmptyMatch(){
	let hps=document.querySelectorAll(".hp");
	hps=Array.from(hps);
	if(hps.every(hp=>{return hp.innerText==="0"})){
		setTimeout(redirect,1000);
        alert(`The match is empty! Returning to home page after clicking ok on this alert`)
	}
}


//Global variable to store the index of the player's selected target card.
let targetedCardIndex=null;
//Global variable to store the index of the player's active card.
let activeCardIndex=null;

//Initial setup on page load.
setCardsAspectRatio();
displayTurn(nextActioningPlayerUid);
applyCardCSS();
checkForEmptyMatch();
//Recalculate card aspect ratios when the browser window is resized.
window.addEventListener("resize",setCardsAspectRatio);