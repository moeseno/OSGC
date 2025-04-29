let cardFinder={
    Card:{className:"default",cardName:"Card"},
    None:{className:"none",cardName:"None"},
    Card2:{className:"default2",cardName:"Card2"},
    Card3:{className:"default3",cardName:"Card3"},
    Card4:{className:"default4",cardName:"Card4"},
    Card5:{className:"default5",cardName:"Card5"},
    Card6:{className:"default6",cardName:"Card6"},
    Card7:{className:"default7",cardName:"Card7"},
    Card8:{className:"default8",cardName:"Card8"},
    Card9:{className:"default9",cardName:"Card9"},
    Cardq:{className:"defaultq",cardName:"Cardq"},
    Cardw:{className:"defaultw",cardName:"Cardw"},
    Carde:{className:"defaulte",cardName:"Carde"},
    Cardr:{className:"defaultr",cardName:"Cardr"},
    Cardt:{className:"defaultt",cardName:"Cardt"},
    Cardy:{className:"defaulty",cardName:"Cardy"},
};

async function pull(amount){
    let pulledCardsContainer=document.getElementsByClassName("pulled-cards-container")[0];
    pulledCardsContainer.innerHTML="";
	const payload={
        amount:amount
    };
    const response=await fetch('/gacha',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(payload)
    });

    let pulledCards=await response.json();

    if (response.ok) {
        displayPulledCards(pulledCards,amount);
    }else{
    	alert(`error occured or sth`);
    };
};

function displayPulledCards(pulledCards,amount){
    let pulledCardsContainer=document.getElementsByClassName("pulled-cards-container")[0];
    for(let key in pulledCards){
        if (pulledCards.hasOwnProperty(key)){
            for (var i=pulledCards[key]-1;i>=0;i--) {
                let pulledCard=document.createElement("div");
                pulledCard.classList.add(cardFinder[key].className);
                pulledCard.classList.add("card");

                pulledCardsContainer.appendChild(pulledCard);
                setCardAspectRatio(pulledCard);
            }
        }
    }
    setTimeout(()=>{
        alert(`successfully pulled ${amount} times`);
    },
    100);
}

function setCardAspectRatio(card){
    console.log(card)
    let height=card.offsetHeight;
    let width=0.714*height;
    card.style.width=width+"px";
}

window.addEventListener("resize",()=>{
    let pulledCards=document.getElementsByClassName("card");
    for (var i=pulledCards.length-1;i>=0;i--){
        setCardAspectRatio(pulledCards[i]);
    }
})