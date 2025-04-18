console.log(uid);
console.log(allOwnedCards);
console.log(currentSelectedCards);
console.log(currentNonSelectedCards);
console.log(notEnoughCards);
console.log(validationFailed);

let cardFinder={
	Card:{
		className:"default",
		cardName:"Card"
	},
	None:{
		className:"none",
		cardName:"None"
	},
	Card2:{
		className:"default2",
		cardName:"Card2"
	}
};

function renderSelectedCards(){
	let keys=Object.keys(currentSelectedCards);
	if(keys.length===0){
		currentSelectedCards={None:3};
		keys=Object.keys(currentSelectedCards);
	};
	let fragment=document.createDocumentFragment();
	let container=document.getElementsByClassName("selected-cards")[0]
	//loop through all cards in selected cards
	for(var cardKeyIndex=0;cardKeyIndex<keys.length;cardKeyIndex++){
		let cardKey=keys[cardKeyIndex]
		let cardAmount=currentSelectedCards[cardKey]
		//create a div for each card owned
		for(var cardAmountCounter=0;cardAmountCounter<cardAmount;cardAmountCounter++){
			let newCard=document.createElement('div');
			newCard.classList.add(cardFinder[cardKey].className);
			newCard.innerHTML=cardFinder[cardKey]["cardName"];

			newCard.setAttribute("onclick","moveCardToSelectedSlot(lastClickedCardData,this)")

			fragment.appendChild(newCard)
		};
	};
	container.appendChild(fragment);
};



function renderNonSelectedCards(){
	let keys=Object.keys(currentNonSelectedCards);
	if(keys.length===0){
		currentNonSelectedCards={None:1};
		keys=Object.keys(currentNonSelectedCards);
	};
	let container=document.getElementsByClassName("non-selected-cards")[0]
	//loop through all cards in non selected cards
	for(var cardKeyIndex=0;cardKeyIndex<keys.length;cardKeyIndex++){
		//set card key and amount
		let cardKey=keys[cardKeyIndex];
		let cardAmount=currentNonSelectedCards[cardKey];
		let cardName=cardFinder[cardKey].cardName;

		//make divs
		let newCard=document.createElement('div');
		newCard.classList.add(cardFinder[cardKey].className);
		let cardNameDiv=document.createElement("div");
		cardNameDiv.innerHTML=cardName;
		let cardAmountDiv=document.createElement("div");
		cardAmountDiv.innerHTML=cardAmount;

		cardAmountDiv.classList.add("card-amount-display");

		//add data
		newCard.setAttribute("data-amount",cardAmount);
		newCard.setAttribute("data-name",cardFinder[cardKey].cardName);

		//append divs
		newCard.appendChild(cardNameDiv);
		newCard.appendChild(cardAmountDiv);

		newCard.setAttribute("onclick","trackLastClickedCard(this)");

		container.appendChild(newCard);
	};	
};



function setSlotNumbers(){
	let cardSlotsContainer=document.getElementsByClassName("selected-cards")[0];
	let cardSlots=cardSlotsContainer.children;

	for (var i=0;i<cardSlots.length;i++){
		cardSlots[i].setAttribute("name",`slot${i+1}`)
	}
};



function trackLastClickedCard(clickedCard) {
	let clickedCardClass=clickedCard.classList[0];
    let clickedCardKey=null;
    for(let key in cardFinder){
        if(cardFinder[key].className===clickedCardClass){
            clickedCardKey=key;
            break;
        }
    }

    //Does the card have any amount left in our data?
    if (clickedCardKey&&currentNonSelectedCards[clickedCardKey]>0){
        lastClickedCardData={
            key:clickedCardKey,
            className:cardFinder[clickedCardKey].className,
            cardName:cardFinder[clickedCardKey].cardName
        };
    }else{
        lastClickedCardData=null;
    }
};



function updateNonSelectedCardDisplay(cardKey) {
    let cardData=cardFinder[cardKey];
    // Don't try to update 'None' or unknown cards in the list
    if (!cardData||cardKey==='None') {
        return;
    }

    let cardElement=document.querySelector(`.non-selected-cards .${cardData.className}`);

    let amountDisplay=cardElement.querySelector('.card-amount-display');
    let currentAmount=currentNonSelectedCards[cardKey]||0;

    if (amountDisplay) {
        amountDisplay.innerHTML=currentAmount;
    }
    cardElement.setAttribute('data-amount',currentAmount);

}



function moveCardToSelectedSlot(cardData,slot){
    //If no card was properly selected before clicking the slot, do nothing.
    if(cardData===null||cardData.key===null){
        // Need to find out what's currently in the slot
        let slottedCardClass=slot.classList[0];
        let slottedCardKey=null;

        for (let key in cardFinder) {
            if (cardFinder[key].className===slottedCardClass) {
                slottedCardKey=key;
                break;
            }
        }

        if (slottedCardKey === null || slottedCardKey === 'None') {
            return;
        }

        // Return the card to the pool
        // Initialize count if needed
        if (!currentNonSelectedCards[slottedCardKey]) {
            currentNonSelectedCards[slottedCardKey] = 0;
        }
        currentNonSelectedCards[slottedCardKey]++;
        updateNonSelectedCardDisplay(slottedCardKey);

        let noneCardInfo=cardFinder['None'];
        slot.className='';
        slot.classList.add(noneCardInfo.className);
        slot.innerHTML=noneCardInfo.cardName;

        // Exit the function after handling unselect
        return;
    }

    //get slotted card data
    let slottedCardClass=slot.classList[0];
    let slottedCardKey=null;
    let otherSlottedCardInfo=null;

    // Find the key and details matching the slot's current class
    for(let key in cardFinder){
        if(cardFinder[key].className===slottedCardClass){
            slottedCardKey=key;
            //className and cardName
            otherSlottedCardData=cardFinder[key];
            break;
        }
    }

    //if cant identify slotted card
    if (slottedCardKey===null){
         return;
    }

    // Create the object holding data for the card in the slot
    let slottedCardData={
        key:slottedCardKey,
        className:otherSlottedCardData.className, 
        cardName:otherSlottedCardData.cardName
    };

    currentNonSelectedCards[cardData.key]--;

    updateNonSelectedCardDisplay(cardData.key);

    if(slottedCardData.key!=='None'){
        // Initialize count if it wasn't in the list before
        if (!currentNonSelectedCards[slottedCardData.key]) {
            currentNonSelectedCards[slottedCardData.key] = 0;
        }
        currentNonSelectedCards[slottedCardData.key]++;
        updateNonSelectedCardDisplay(slottedCardData.key);
    }

    slot.className='';
    slot.classList.add(cardData.className);
    slot.innerHTML=cardData.cardName;

    lastClickedCardData=null;
}



function clearSelection(){
	lastClickedCardData=null;
};

renderSelectedCards();
renderNonSelectedCards();

setSlotNumbers();