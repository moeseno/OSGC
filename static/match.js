//sets 1 card aspect ratio
function setCardAspectRatio(card) {
	let height=card.offsetHeight;
	let width=0.714*height;
	card.style.width=width+"px";
};

//calls function above to set all cards aspect ratio
function setCardsAspectRatio(){
	let cards=document.getElementsByClassName("card")
	for (var i=cards.length-1;i>=0; i--){
		setCardAspectRatio(cards[i]);
	};
};

//shows/hides the chatbox
function toggleChatBox(){
	let chatBox=document.getElementsByClassName("chat-container")[0];
	let computedStyle=getComputedStyle(chatBox);
	if (computedStyle.display=="none"){
		chatBox.style.display="block";
	}else if(computedStyle.display=="block"){
		chatBox.style.display="none";
	};
};

//sends messages thru websocket
function send(){
	//get input
	let text=document.getElementsByClassName("chat-input")[0].value;
	
	//check for not allowed characters and empty strings
	if (text==''){
		alert("enter something before sending");
		return;
	}else if (text.includes("<")||text.includes(">")){
		alert("illegal character");
		return;
	}
	//creates message
	let message={
		user:document.getElementsByClassName("username")[0].innerHTML,
		text:text
	};
	//check for websocket state before sending and clearing chat input
	if (chatSocket.readyState===WebSocket.OPEN){
		chatSocket.send(JSON.stringify(message));
		document.getElementsByClassName("chat-input")[0].value = "";
	}else{
        console.error("WebSocket connection is not open.");
    };
};

//adds message to message box
function addMessage(text){
	let message=document.createElement("div");
	let chatBox=document.getElementsByClassName("chatbox")[0];
	message.innerHTML=text;
	message.classList.add("message");
	chatBox.append(message);
};

function exit(){
	if (chatSocket.readyState===WebSocket.OPEN){
		chatSocket.send(JSON.stringify(null));
	};	
};

function redirect(){
	window.location.href="/";
};


let chatSocket=new WebSocket("wss://"+location.host+"/chat"+window.location.pathname);

//tell backend sockets are open
chatSocket.addEventListener("open",(event)=>{
	let message={
		user:document.getElementsByClassName("username")[0].innerHTML,
		text:"This user has connected!"
	};
	setTimeout(()=>{
		chatSocket.send(JSON.stringify(message));
	},1000);
	
});
//handles message recieving
chatSocket.addEventListener("message",(event)=>{
    try{
        let receivedMessage=JSON.parse(event.data);
        if (receivedMessage.startsWith("SERVER: ")&&receivedMessage.endsWith(" has disconnected, redirecting in 5 seconds...")){
        	addMessage(receivedMessage);
        	setTimeout(redirect,5000);
        }else{
        	addMessage(receivedMessage);
        };
    }catch(error){
        console.error("Error parsing message:",error);
    };
});



setCardsAspectRatio();
window.addEventListener("resize", setCardsAspectRatio);