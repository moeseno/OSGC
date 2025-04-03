//sets the width of a single card based on its height to maintain aspect ratio
function setCardAspectRatio(card) {
	//get current height
	let height=card.offsetHeight;
	//calculate width based on fixed ratio (0.714)
	let width=0.714*height;
	//apply calculated width
	card.style.width=width+"px";
};



//applies aspect ratio calculation to all elements with class "card"
function setCardsAspectRatio(){
	//get all card elements
	let cards=document.getElementsByClassName("card")
	//loop through cards and apply individual aspect ratio setting
	for (var i=cards.length-1;i>=0; i--){
		setCardAspectRatio(cards[i]);
	};
};



//toggles the visibility of the chat box container
function toggleChatBox(){
	//get chat container element
	let chatBox=document.getElementsByClassName("chat-container")[0];
	//get its current computed display style
	let computedStyle=getComputedStyle(chatBox);
	//if hidden, show it
	if (computedStyle.display=="none"){
		chatBox.style.display="block";
	//if shown, hide it
	}else if(computedStyle.display=="block"){
		chatBox.style.display="none";
	};
};



//sends a chat message via websocket
function send(){
	//get chat input element and its value
	let textInput=document.getElementsByClassName("chat-input")[0];
	let text=textInput.value;

	//validate input: not empty
	if (text==''){
		alert("enter something before sending");
		return;
	//validate input: no html tags (basic check)
	}else if (text.includes("<")||text.includes(">")){
		alert("illegal character");
		return;
	}
	//prepare chat message object
	let message={
		type:"chat",
		text:text
	};
	//send message if socket is open
	if (socket && socket.readyState===WebSocket.OPEN){
		socket.send(JSON.stringify(message));
		//clear input field after sending
		document.getElementsByClassName("chat-input")[0].value = "";
	}else{
		//alert if connection is not open
        alert("WebSocket connection is not open.");
    };
};



//adds a message string to the chat display area
function addMessage(text){
	//create a new div for the message
	let message=document.createElement("div");
	//get the chatbox display area
	let chatBox=document.getElementsByClassName("chatbox")[0];
	//set the message content
	message.innerHTML=text;
	//add css class for styling
	message.classList.add("message");
	//append the new message div to the chatbox
	chatBox.append(message);
};



//sets the visual target indicator on an opponent's card
function setTarget(clickedCard,targetNumber){
	//get all opponent card elements
	let opponentCards=document.getElementsByClassName("opponent-card")
	for (var i = opponentCards.length - 1; i >= 0; i--) {
		opponentCards[i].classList.remove("targeted");
	};
	//add "targeted" class to the clicked card
	clickedCard.classList.add("targeted");
	//store the index of the targeted card globally
    targetedCardIndex=targetNumber;
};



//sends an ability usage action via websocket
function useAbility(attackingPlayerUid,attackingCardIndex,abilityNumber,targetedPlayerUid){

	//Check if it is the current player's turn
    if (attackingPlayerUid !== nextActioningPlayerUid) {
        alert("It's not your turn!");
        return;
    }

	//prepare action message object, including the globally stored target index
	let message={
		type:"action",
		attackingPlayerUid:attackingPlayerUid,
		attackingCardIndex:attackingCardIndex,
		targetedPlayerUid:targetedPlayerUid,
		targetedCardIndex:targetedCardIndex, //uses the globally set index
		abilityNumber:abilityNumber
	};
	//send message if socket is open
	if (socket && socket.readyState===WebSocket.OPEN){
		socket.send(JSON.stringify(message));
	}else{
		//alert if connection is not open
        alert("WebSocket connection is not open.");
    };
}



//updates the displayed HP of a card based on action data from server
function setHp(actionData) {
	//check if the current player's card was targeted
	if (actionData["targeted_player_uid"]===uid){

		//get all player card elements
		let cards=document.getElementsByClassName("player-card")
		//get the collection of hp elements
		let hp=cards[actionData["targeted_card_index"]].getElementsByClassName("hp")[0]
		//attempt to set innerHTML on the collection (original error)
		hp.innerHTML=actionData["target_hp"]

	//check if the current player was the attacker (meaning opponent's card was targeted)
	}else if(actionData["attacking_player_uid"]===uid){

		//get all opponent card elements
		let cards=document.getElementsByClassName("opponent-card")
		//get the FIRST hp element 
		let hp=cards[actionData["targeted_card_index"]].getElementsByClassName("hp")[0]
		//update the hp display
		hp.innerHTML=actionData["target_hp"]
	}
}



//closes the websocket connection and redirects the user
function exit(){
	//close socket gracefully if open
	if (socket && socket.readyState===WebSocket.OPEN){
        socket.close(1000, "User exited"); //1000 is normal closure code
	}
	//redirect to homepage
	redirect();
};



//redirects the browser to the homepage
function redirect(){
	window.location.href="/";
};


//determine websocket protocol (ws or wss)
let protocol=window.location.protocol==="https:"?"wss://":"ws://";
//construct websocket url using host, path, and matchID from html template
let wsURL=protocol+location.host+"/chat/match/"+matchID;
//create new websocket connection
let socket=new WebSocket(wsURL);



//event listener for when the websocket connection opens
socket.addEventListener("open",(event)=>{
	//prepare authentication message with user's uid (from html template)
	let authMessage={
		type:"auth",
		uid:uid
	};
	//send authentication message immediately after opening
	if (socket.readyState===WebSocket.OPEN) {
	    socket.send(JSON.stringify(authMessage));
    }
});



//event listener for messages received from the server
socket.addEventListener("message",(event)=>{
    //safely parse incoming json data
    try{
        let receivedMessage=JSON.parse(event.data);
        //check for server disconnect message format
        if (typeof receivedMessage==="string" &&
            receivedMessage.startsWith("SERVER: ") &&
            receivedMessage.endsWith(" has disconnected, redirecting in 5 seconds...")){
            //display message and schedule redirect
            addMessage(receivedMessage);
        	setTimeout(redirect,5000);
        //check for regular chat message (string)
        }else if(typeof receivedMessage==="string"){
        	//display chat message
        	addMessage(receivedMessage);
        //check for action result message (object)
        }else if(typeof receivedMessage==="object"){

        	if(receivedMessage["type"]==="action"){
        		//update card hp based on action data
        		setHp(receivedMessage);
        	}else if(receivedMessage["type"]==="turn"){
                // Update whose turn it is
                nextActioningPlayerUid=receivedMessage["next_actioning_player_uid"];
                console.log("It is now player " + nextActioningPlayerUid + "'s turn.");
            }
        	
        }
    //ignore messages that fail parsing or don't match expected formats
    }catch(error){};
});



//initialize the index for the targeted card (used by setTarget and useAbility)
let targetedCardIndex=0;
//set initial card aspect ratios on page load
setCardsAspectRatio();
//add event listener to reset aspect ratios on window resize
window.addEventListener("resize", setCardsAspectRatio);