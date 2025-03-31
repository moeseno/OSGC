function setCardAspectRatio(card) {
	let height=card.offsetHeight;
	let width=0.714*height;
	card.style.width=width+"px";
};

function setCardsAspectRatio(){ 
	let cards=document.getElementsByClassName("card")
	for (var i=cards.length-1;i>=0; i--){
		setCardAspectRatio(cards[i]);
	};
};

function toggleChatBox(){ 
	let chatBox=document.getElementsByClassName("chat-container")[0];
	let computedStyle=getComputedStyle(chatBox);
	if (computedStyle.display=="none"){
		chatBox.style.display="block";
	}else if(computedStyle.display=="block"){
		chatBox.style.display="none";
	};
};

function send(){
	let textInput=document.getElementsByClassName("chat-input")[0];
	let text=textInput.value;

	if (text==''){
		alert("enter something before sending");
		return;
	}else if (text.includes("<")||text.includes(">")){
		alert("illegal character");
		return;
	}
	let message={
		type:"chat",
		text:text
	};
	if (chatSocket && chatSocket.readyState===WebSocket.OPEN){
		chatSocket.send(JSON.stringify(message));
		document.getElementsByClassName("chat-input")[0].value = "";
	}else{
        alert("WebSocket connection is not open.");
    };
};

function addMessage(text){
	let message=document.createElement("div");
	let chatBox=document.getElementsByClassName("chatbox")[0];
	message.innerHTML=text;
	message.classList.add("message");
	chatBox.append(message);
};

function exit(){
	if (chatSocket && chatSocket.readyState===WebSocket.OPEN){
        chatSocket.close(1000, "User exited");
	}
	redirect();
};

function redirect(){
	window.location.href="/";
};


let protocol=window.location.protocol==="https:"?"wss://":"ws://";
let wsURL=protocol+location.host+"/chat/match/"+matchID;
let chatSocket=new WebSocket(wsURL);



chatSocket.addEventListener("open",(event)=>{
	let authMessage={
		type:"auth",
		uid:uid
	};
	if (chatSocket.readyState===WebSocket.OPEN) {
	    chatSocket.send(JSON.stringify(authMessage));
    }
});

chatSocket.addEventListener("message",(event)=>{
    try{
        let receivedMessage=JSON.parse(event.data);
        console.log(receivedMessage)
        if (typeof receivedMessage === 'string' &&
            receivedMessage.startsWith("SERVER: ") &&
            receivedMessage.endsWith(" has disconnected, redirecting in 5 seconds...")){
            addMessage(receivedMessage);
        	setTimeout(redirect,5000);
        } else if (typeof receivedMessage === 'string') {
        	addMessage(receivedMessage);
        }
    }catch(error){
    };
});


setCardsAspectRatio();
window.addEventListener("resize", setCardsAspectRatio);