let lastClickedCardData=null;


//Sets the width of a single card based on its height to maintain aspect ratio.
function setCardAspectRatio(card){
    let height=card.offsetHeight;
    let width=0.714*height;
    card.style.width=width+"px";
}

function clearSelection() {
    lastClickedCardData=null;
}

// Renders the selection slots based on initial CARD COUNTS state
function renderSelectedCards(){
    // Assumes currentSelectedCards holds counts: {'Card': 2, 'None': 1}
    if(typeof currentSelectedCards!=='object'||currentSelectedCards===null){
        currentSelectedCards={None:3}; // Default if invalid
    }

    let selectedCardValues=Object.values(currentSelectedCards);

    // Default to 3 'None' if initial object is empty
    if(selectedCardValues.length===0){
        currentSelectedCards={None:3};
        selectedCardValues=Object.values(currentSelectedCards);
    }
    let fragment=document.createDocumentFragment();
    let container=document.querySelector(".selected-cards"); // Use querySelector
    if(!container)return;
    container.innerHTML=''; // Clear previous content

    // Loop through card types in the initial selected data
    for(let i=0;i<selectedCardValues.length;i++){
        let cardValue=selectedCardValues[i];
        let cardDefinition=cardFinder[cardValue];


        // Use None definition if card type is unknown
        if(!cardDefinition){
            cardValue='None';
            cardDefinition=cardFinder[cardValue];
            // If original key wasn't 'None', assume count was 1 for unknown card
            if(selectedCardValues[i]!=='None') cardCount=1;
        }
        // Create an element for each instance of a card
        let slotElement=document.createElement('div');
        // Add class based on card type (will be updated by setSlotNumbers later)
        slotElement.classList.add(cardDefinition.className);
        slotElement.innerHTML=cardDefinition.cardName;
        // Allow clicking the slot to move a selected card into it
        slotElement.setAttribute("onclick","moveCardToSelectedSlot(lastClickedCardData,this)");
        fragment.appendChild(slotElement);
    }
    container.appendChild(fragment);
}


// Renders the list of available cards (non-selected pool)
function renderNonSelectedCards(){
    // Assumes currentNonSelectedCards holds counts: {'Card': 5}
    if(typeof currentNonSelectedCards!=='object'||currentNonSelectedCards===null){
        currentNonSelectedCards={};
    }
    let nonSelectedCardKeys=Object.keys(currentNonSelectedCards);
    let container=document.querySelector(".non-selected-cards");
    if(!container)return;
    container.innerHTML=''; // Clear previous content

    for(let i=0;i<nonSelectedCardKeys.length;i++){
        let cardKey=nonSelectedCardKeys[i];
        let cardCount=currentNonSelectedCards[cardKey];
        let cardDefinition=cardFinder[cardKey];
        // Skip None, undefined, or zero-count cards in available list
        if(cardKey==='None'||!cardDefinition||cardCount<=0){
            continue;
        }
        let cardElement=document.createElement('div');
        cardElement.classList.add(cardDefinition.className);
        cardElement.classList.add('available-card-item');
        let nameElement=document.createElement("div");
        nameElement.innerHTML=cardDefinition.cardName;
        let countElement=document.createElement("div");
        countElement.innerHTML=cardCount;
        countElement.classList.add("card-amount-display");
        cardElement.setAttribute("data-amount",cardCount);
        cardElement.setAttribute("data-key",cardKey);
        cardElement.appendChild(nameElement);
        cardElement.appendChild(countElement);
        cardElement.setAttribute("onclick",`trackLastClickedCard('${cardKey}')`);
        container.appendChild(cardElement);
    }
}


// Adds slot-specific attributes and hidden inputs AFTER initial render
function setSlotNumbers(){
    let container=document.querySelector(".selected-cards");
    if(!container) return;
    let slotElements=container.children;
    for(let i=0;i<slotElements.length;i++){
        slotElements[i].classList.add("card-slot"); // Add base slot class
        // Add hidden input for tracking state and submission
        let hiddenInput=document.createElement("input");
        hiddenInput.setAttribute("type","hidden");
        hiddenInput.setAttribute("name",`slot${i+1}`); // Name based on position
        // Determine initial value based on rendered card class (less reliable but matches original logic)
        let currentClass=slotElements[i].classList[0] === 'card-slot' ? slotElements[i].classList[1] : slotElements[i].classList[0];
        let initialValue='None';
        for(let key in cardFinder){
            if(cardFinder[key].className===currentClass){
                initialValue=key;
                break;
            }
        }
        hiddenInput.setAttribute("value",initialValue);
        // Avoid adding duplicate input if somehow called twice
        if(!slotElements[i].querySelector('input[type="hidden"]')){
            slotElements[i].appendChild(hiddenInput);
        }
    }
}


// Stores data of the last available card clicked (if count > 0)
function trackLastClickedCard(clickedCardKey){
    if(clickedCardKey&&cardFinder[clickedCardKey]&&currentNonSelectedCards[clickedCardKey]>0){
        lastClickedCardData={
            key:clickedCardKey,
            className:cardFinder[clickedCardKey].className,
            cardName:cardFinder[clickedCardKey].cardName
        };
        document.querySelectorAll('.available-card-item.selected-for-move').forEach(el=>el.classList.remove('selected-for-move'));
        let clickedElement=document.querySelector(`.non-selected-cards [data-key="${clickedCardKey}"]`);
        if(clickedElement)clickedElement.classList.add('selected-for-move');
    }else{
        lastClickedCardData=null;
         document.querySelectorAll('.available-card-item.selected-for-move').forEach(el=>el.classList.remove('selected-for-move'));
    }
}


// Updates the display count or adds/removes an available card element
function updateNonSelectedCardDisplay(cardKeyToUpdate){
    let cardDefinition=cardFinder[cardKeyToUpdate];
    if(!cardDefinition||cardKeyToUpdate==='None'){return};
    let container=document.querySelector(".non-selected-cards");
    if(!container)return;
    let cardElement=container.querySelector(`[data-key="${cardKeyToUpdate}"]`);
    let newCount=currentNonSelectedCards[cardKeyToUpdate]||0;

    if(newCount<=0){
        if(cardElement)cardElement.remove();
    }else{
        if(cardElement){
            let countDisplay=cardElement.querySelector('.card-amount-display');
            if(countDisplay)countDisplay.innerHTML=newCount;
            cardElement.setAttribute('data-amount',newCount);
        }else{
            let newCardElement=document.createElement('div');
            newCardElement.classList.add(cardDefinition.className);
            newCardElement.classList.add('available-card-item');
            let nameElement=document.createElement("div");
            nameElement.innerHTML=cardDefinition.cardName;
            let countElement=document.createElement("div");
            countElement.innerHTML=newCount;
            countElement.classList.add("card-amount-display");
            newCardElement.setAttribute("data-amount",newCount);
            newCardElement.setAttribute("data-key",cardKeyToUpdate);
            newCardElement.appendChild(nameElement);
            newCardElement.appendChild(countElement);
            newCardElement.setAttribute("onclick",`trackLastClickedCard('${cardKeyToUpdate}')`);
            container.appendChild(newCardElement);
        }
    }
}


// Handles moving a card between the available pool and a selected slot
function moveCardToSelectedSlot(clickedCardData,targetSlotElement){
    if(!targetSlotElement)return;
    let hiddenInput=targetSlotElement.querySelector('input[type="hidden"]');
    // It's critical setSlotNumbers runs first to ensure hidden input exists
    if(!hiddenInput){console.error("Missing hidden input in slot!"); return;}
    let currentSlotCardKey=hiddenInput.value;
    let slotName=hiddenInput.name;

    // CASE 1: Return card FROM slot
    if(clickedCardData===null||clickedCardData.key===null){
        if(currentSlotCardKey==='None')return;
        let returningCardDefinition=cardFinder[currentSlotCardKey];
        if(returningCardDefinition){
            if(!currentNonSelectedCards[currentSlotCardKey])currentNonSelectedCards[currentSlotCardKey]=0;
            currentNonSelectedCards[currentSlotCardKey]++;
            updateNonSelectedCardDisplay(currentSlotCardKey);
        }
        let noneDefinition=cardFinder['None'];
        // Reset class list properly
        targetSlotElement.className='card-slot '+noneDefinition.className;
        targetSlotElement.innerHTML=noneDefinition.cardName;
        targetSlotElement.appendChild(hiddenInput); // Re-append
        hiddenInput.value='None';
        return;
    }

    // CASE 2: Move card INTO slot
    if(clickedCardData.key===currentSlotCardKey){
        clearSelection();
        return;
    }
    if(currentNonSelectedCards[clickedCardData.key]>0){
        currentNonSelectedCards[clickedCardData.key]--;
        updateNonSelectedCardDisplay(clickedCardData.key);
        if(currentSlotCardKey!=='None'){
            let currentSlotDefinition=cardFinder[currentSlotCardKey];
            if(currentSlotDefinition){
                 if(!currentNonSelectedCards[currentSlotCardKey])currentNonSelectedCards[currentSlotCardKey]=0;
                 currentNonSelectedCards[currentSlotCardKey]++;
                 updateNonSelectedCardDisplay(currentSlotCardKey);
            }
        }
        // Reset class list properly
        targetSlotElement.className='card-slot '+clickedCardData.className;
        targetSlotElement.innerHTML=clickedCardData.cardName;
        targetSlotElement.appendChild(hiddenInput); // Re-append
        hiddenInput.value=clickedCardData.key;
        clearSelection();
    }else{
        clearSelection();
    }
}


// Submits the current selection state to the server
async function handleInventorySubmit(event){
    event.preventDefault();
    let selectedData={};
    // Gather data from hidden inputs (state is tracked there now)
    document.querySelectorAll('.selected-cards .card-slot').forEach(slot=>{
        let hiddenInput=slot.querySelector('input[type="hidden"]');
        if(hiddenInput&&hiddenInput.name)selectedData[hiddenInput.name]=hiddenInput.value;
    });
    let payload={
        uid:(typeof uid!=='undefined'?uid:null),
        selected_cards:selectedData, // Send slot assignments
        current_non_selected_cards:currentNonSelectedCards, // Send current available counts
        all_owned_cards:(typeof allOwnedCards!=='undefined'?allOwnedCards:null) // Send initial total counts
    };
    if(!payload.uid||!payload.all_owned_cards){alert("Error");return;}

    let success=false;
    try{
        let response=await fetch('/inventory',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(payload)
        });
        if(response.ok){
            let result=await response.json();
            success=result===true;
        }else{
             console.error('HTTP Error:',response.status);
        }
    }catch(error){
        console.error('Network Error:',error);
    }

    if(success){alert("Selection Saved!");}
    else{alert("Error saving selection.");}
}


document.addEventListener('DOMContentLoaded',()=>{
    if(typeof currentSelectedCards==='undefined'||typeof currentNonSelectedCards==='undefined'){
         console.error("Initial card data missing.");
         return;
    }
    // Initial render based on counts
    renderSelectedCards();
    renderNonSelectedCards();
    // Add hidden inputs and slot classes AFTER initial render
    setSlotNumbers();
    document.querySelectorAll(".card-slot").forEach(setCardAspectRatio);
    document.querySelectorAll(".available-card-item").forEach(setCardAspectRatio);

    let form=document.querySelector('.inventory-form');
    if(form)form.addEventListener('submit',handleInventorySubmit);
});

window.addEventListener("resize",()=>{
    document.querySelectorAll(".card-slot").forEach(setCardAspectRatio);
    document.querySelectorAll(".available-card-item").forEach(setCardAspectRatio);
});