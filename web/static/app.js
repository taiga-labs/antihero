let tg = window.Telegram.WebApp;
tg.expand()
tg.MainButton.textColor = "#FFFFFF";
tg.MainButton.color = "#FF00FF"

const urlParams = new URLSearchParams(window.location.search);
const game_uuid = urlParams.get('uuid')
const nft_id = urlParams.get('nft_id');


let btn_start = document.getElementById("btn_start")
btn_start.addEventListener("click", function(){
	fetch('/start', {
   	        method: 'POST',
   	        headers: {
   	            'Accept': 'application/json',
   	            'Content-Type': 'application/json',
   	        	},
   	        	body: JSON.stringify({
   	        		uuid: game_uuid,
   	        		nft_id: nft_id
   	        	})
   	    	})
   	    	.catch(error => alert(error))
})

let btn_score = document.getElementById("btn_score")
btn_score.addEventListener("click", function(){
	fetch('/score', {
   	        method: 'POST',
   	        headers: {
   	            'Accept': 'application/json',
   	            'Content-Type': 'application/json',
   	        	},
   	        	body: JSON.stringify({
   	        		query_id: tg.initDataUnsafe.query_id,
   	        		uuid: game_uuid,
   	        		nft_id: nft_id,
   	            	score: "150",
   	        	})
   	    	})
   	    	.catch(error => alert(error));
   	tg.MainButton.setText("Сообщение отправлено!!");
   	tg.MainButton.show();
})


let btn_show = document.getElementById("btn_show");
let tgdata = window.Telegram.WebApp.initData;
// let tgdata = tg.initDataUnsafe.user.id
btn_show.addEventListener("click", function(){
	console.log("PATH ", __dirname)
    alert(tgdata)
});