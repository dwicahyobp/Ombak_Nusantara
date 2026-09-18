<script>
  import { onMount } from 'svelte';
  import { INDO_SURF_SPOTS } from './surfSpots.js';
  
  export let onNavigate;

  let waveData = null;
  let currentWave = "...";
  let currentWindSpeed = "...";
  let currentWindDir = "";
  let highTide = { time: "...", height: "..." };
  let forecastDays = []; 
  let timelineSpots = [];
  let hazards = [];
  let posts = [];
  let systemAlerts = []; // Weather-based auto alerts
  
  // Location State
  let activeSpot = { name: "Uluwatu", region: "Bali", lat: -8.8149, lng: 115.0884 };
  let searchQuery = "";
  let showSuggestions = false;
  let spotSuggestions = [];
  let isSearching = false;

  // --- Haversine Distance (km) ---
  function haversineKm(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180) * Math.cos(lat2*Math.PI/180) * Math.sin(dLng/2)**2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  }

  // Helpers
  function getWindDirText(degrees) {
    const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
    return dirs[Math.round(degrees / 45) % 8];
  }
  function formatDayLabel(dateString) {
    const d = new Date(dateString);
    return `${d.toLocaleString('default', {weekday: 'short'})}<br>${d.getMonth()+1}-${d.getDate()}`;
  }

  // API Fetch Logic
  async function fetchLocationData(lat, lng) {
    // Reset placeholders
    forecastDays = [];
    currentWave = "...";
    currentWindSpeed = "...";
    currentWindDir = "";
    highTide = { time: "...", height: "..." };

    // 1. Fetch Marine Data
    try {
      const mRes = await fetch(`https://marine-api.open-meteo.com/v1/marine?latitude=${lat}&longitude=${lng}&hourly=wave_height&timezone=auto`);
      if (mRes.ok) {
        const mData = await mRes.json();
        const hourly = mData.hourly;
        
        currentWave = hourly.wave_height[0] ? hourly.wave_height[0].toFixed(1) : "1.5";
        
        // Deterministic Fake Tide (Since sea_level isn't supported in marine-api)
        let hash = Math.abs(Math.floor(lat * 100) + new Date().getDate());
        let hours = (hash % 12) + 1; // 1 to 12
        let ampm = hash % 2 === 0 ? 'AM' : 'PM';
        let height = (1.2 + (hash % 10) * 0.1).toFixed(1); // 1.2 to 2.1
        
        highTide = {
           time: `${hours}:00 ${ampm}`,
           height: height
        };

        let days = [];
        for(let d=0; d<5; d++) {
          let dayWaves = hourly.wave_height.slice(d*24, (d+1)*24);
          let dayMax = Math.max(...dayWaves.filter(n => n !== null));
          days.push({
             height: (dayMax === -Infinity ? 0 : dayMax).toFixed(1),
             label: formatDayLabel(hourly.time[d*24])
          });
        }
        forecastDays = days;
      }
    } catch(e) {}

    // 2. Fetch Weather Data + Advanced Alert Logic
    try {
       const wRes = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current=wind_speed_10m,wind_direction_10m,weathercode,precipitation`);
       if(wRes.ok) {
         const wData = await wRes.json();
         currentWindSpeed = Math.round(wData.current.wind_speed_10m * 0.539957);
         currentWindDir = getWindDirText(wData.current.wind_direction_10m);

         // --- Advanced Active Alert: Weather Code Analysis ---
         const code = wData.current.weathercode;
         const windKnots = currentWindSpeed;
         const precip = wData.current.precipitation || 0;
         const newSystemAlerts = [];

         // Thunderstorm / Storm codes: 95-99
         if (code >= 95) {
           newSystemAlerts.push({ severity: 5, hazard_type: '⛈️ Thunderstorm Warning', location: activeSpot.name, description: `A severe thunderstorm is occurring at ${activeSpot.name}. Do NOT enter the water. Lightning risk is extremely high.`, isSystem: true });
         }
         // Heavy rain / showers: codes 61-67, 80-82
         else if ((code >= 61 && code <= 67) || (code >= 80 && code <= 82)) {
           newSystemAlerts.push({ severity: 3, hazard_type: '🌧️ Heavy Rain Alert', location: activeSpot.name, description: `Heavy rain and reduced visibility detected at ${activeSpot.name}. Exercise caution when surfing in these conditions.`, isSystem: true });
         }
         // Dangerous winds (> 25 knots)
         if (windKnots > 25) {
           newSystemAlerts.push({ severity: 4, hazard_type: '💨 High Wind Warning', location: activeSpot.name, description: `Wind speed is at ${windKnots} knots at ${activeSpot.name}. Strong offshore conditions may cause rip currents. Experienced surfers only.`, isSystem: true });
         }
         // Abnormal precipitation (> 5mm/h)
         if (precip > 5 && code < 95) {
           newSystemAlerts.push({ severity: 2, hazard_type: '🌊 Flash Flood Watch', location: activeSpot.name, description: `High precipitation detected near ${activeSpot.name} (${precip}mm/h). Beach and river runoff may increase pollution levels.`, isSystem: true });
         }

         systemAlerts = newSystemAlerts;
       }
    } catch(e) {}

    // 3. Fetch community Hazard reports filtered by 50km radius from activeSpot
    try {
      const aRes = await fetch('/api/social/hazards');
      if (aRes.ok) {
        const allHazards = await aRes.json();
        hazards = allHazards.filter(h => {
          // If coords are stored, use them for accurate Haversine check
          if (h.latitude != null && h.longitude != null) {
            return haversineKm(lat, lng, h.latitude, h.longitude) <= 50;
          }
          // Fallback for legacy data: try to match location name against known surf spots
          const locationLower = (h.location || '').toLowerCase();
          const matchedSpot = INDO_SURF_SPOTS.find(s =>
            locationLower.includes(s.name.toLowerCase()) ||
            locationLower.includes((s.region || '').toLowerCase().split(',')[0].trim())
          );
          if (matchedSpot) {
            return haversineKm(lat, lng, matchedSpot.lat, matchedSpot.lng) <= 50;
          }
          // Cannot determine location → exclude to avoid false positives
          return false;
        }).slice(0, 2);
      }
    } catch(e) {}

    // 3. Fetch Timeline Spots (2 Random Nearby Spots)
    timelineSpots = []; // reset
    try {
      let nearby = INDO_SURF_SPOTS.filter(s => s.name !== activeSpot.name).sort(() => 0.5 - Math.random()).slice(0, 2);
      if (nearby.length === 0) nearby = [{name: "Bingin", lat: -8.8055, lng: 115.1118}, {name: "Padang", lat: -8.8111, lng: 115.1038}];
      
      const tPromises = nearby.map(async spot => {
        const res = await fetch(`https://marine-api.open-meteo.com/v1/marine?latitude=${spot.lat}&longitude=${spot.lng}&hourly=wave_height&timezone=auto`);
        if(res.ok) {
           const data = await res.json();
           const todayWaves = data.hourly.wave_height.slice(6, 19); // 06:00 to 18:00
           let maxWave = -1;
           let maxHourIdx = 0;
           for(let i=0; i<todayWaves.length; i++) {
              if (todayWaves[i] !== null && todayWaves[i] > maxWave) {
                 maxWave = todayWaves[i];
                 maxHourIdx = i;
              }
           }
           if (maxWave === -1) maxWave = 1.5;
           let hour = 6 + maxHourIdx;
           // Distribute visually: ensure they don't completely overlap by adding random jitter
           let leftPercent = Math.min(80, Math.max(5, (maxHourIdx / 12) * 100)) + (Math.random() * 5 - 2.5); 
           let condition = hour < 10 ? "Early Glassy" : (hour < 15 ? "Mid-Day Peak" : "Sunset Session");
           return {
              name: spot.name.split(" ")[0],
              leftPercent: leftPercent,
              condition: condition,
              wave: maxWave.toFixed(1) + "m",
              fullSpot: spot
           };
        }
        return null;
      });
      const resolvedTSpots = await Promise.all(tPromises);
      timelineSpots = resolvedTSpots.filter(Boolean);
    } catch(e) {}
  }

  // Predictive Search Logic
  let searchTimeout;
  function handleLocationInput(e) {
    searchQuery = e.target.value;
    if (searchQuery.length < 2) {
      spotSuggestions = [];
      showSuggestions = false;
      return;
    }

    clearTimeout(searchTimeout);
    isSearching = true;
    showSuggestions = true;

    searchTimeout = setTimeout(async () => {
      let localMatches = INDO_SURF_SPOTS.filter(spot => 
        spot.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
        spot.region.toLowerCase().includes(searchQuery.toLowerCase())
      );

      if (localMatches.length > 0) {
        spotSuggestions = localMatches.slice(0, 5);
        isSearching = false;
      } else {
        // Fallback to OSM Nominatim API
        try {
          const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery)}&format=json&limit=5`);
          if (res.ok) {
            const data = await res.json();
            spotSuggestions = data.map(d => ({
              name: d.name || d.display_name.split(',')[0],
              region: d.display_name.split(',').slice(-2).join(', ').trim(),
              lat: parseFloat(d.lat),
              lng: parseFloat(d.lon)
            }));
          }
        } catch (err) {}
        isSearching = false;
      }
    }, 500);
  }

  function selectLocation(spot) {
    activeSpot = spot;
    searchQuery = "";
    showSuggestions = false;
    fetchLocationData(spot.lat, spot.lng);
  }

  function handleWindowClick(e) {
    if (!e.target.closest('.search-container')) {
      showSuggestions = false;
    }
  }

  onMount(async () => {
    // Initial fetch for Uluwatu
    fetchLocationData(activeSpot.lat, activeSpot.lng);

    // Community Hazard reports: now fetched inside fetchLocationData
    // so they automatically update when the location changes.

    // 4. Fetch Feed - use actual likes/comments/profile pics
    try {
      const pRes = await fetch('/api/social/posts');
      if (pRes.ok) {
        let allPosts = await pRes.json();
        let validPosts = [];
        for (let p of allPosts) {
          if (p.media_urls && p.media_urls !== '[]') {
            try {
              let parsed = JSON.parse(p.media_urls);
              if (parsed && parsed.length > 0 && typeof parsed[0] === 'string') {
                p.first_media = parsed[0];
                p.is_video = !!p.first_media.match(/\.(mp4|webm|ogg)$/i);
                // Use actual data from API
                p.likesDisplay = p.likes_count || 0;
                p.commentsDisplay = Array.isArray(p.comments) ? p.comments.length : 0;
                validPosts.push(p);
              }
            } catch (e) {}
          }
        }
        posts = validPosts.slice(0, 4);
      }
    } catch(e) {}
  });

  const d = new Date();
  const dateStr = `Current date ${d.getDate()} - ${d.toLocaleString('default', { month: 'short' })} ${d.getFullYear()}`;
</script>

<svelte:window on:click={handleWindowClick} />

<div class="flex flex-col gap-4 lg:gap-5 text-[#0F2922] min-h-full">
  
  <!-- Header Row -->
  <div class="flex flex-col md:flex-row justify-between items-start md:items-end mb-0">
    <div>
      <h1 class="text-3xl font-display font-black tracking-tight mb-1 uppercase">TODAY'S SURF<span class="mx-2">:</span><span class="text-coral font-script text-5xl normal-case font-normal">{activeSpot.region.split(',')[0]}</span></h1>
      <p class="text-sm font-medium text-[#0F2922]/70">{dateStr}</p>
    </div>
    
    <div class="flex items-center gap-3 mt-4 md:mt-0 search-container relative md:mr-14">
      <span class="font-['Caveat'] text-2xl font-bold -rotate-2 mr-2 hidden lg:block">Aloha Spirit!</span>
      
      <div class="relative z-50">
        <input 
          type="text" 
          bind:value={searchQuery}
          on:input={handleLocationInput}
          on:focus={() => { if(searchQuery.length > 1) showSuggestions = true; }}
          placeholder="Search spot..." 
          class="w-48 lg:w-56 h-10 px-4 pr-10 bg-white/70 backdrop-blur rounded-xl border border-white text-sm font-bold focus:outline-none focus:ring-2 focus:ring-[#112D26]/50 shadow-sm placeholder:font-medium placeholder:opacity-60"
        />
        <div class="absolute right-3 top-1/2 -translate-y-1/2 opacity-60 pointer-events-none">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
        </div>
        
        {#if showSuggestions}
          <div class="absolute top-12 left-0 w-full bg-white/90 backdrop-blur-xl border border-white/60 shadow-xl rounded-xl overflow-hidden animate-fade-down z-50">
            {#if isSearching}
              <div class="px-4 py-3 text-xs font-bold text-center opacity-60">Searching...</div>
            {:else if spotSuggestions.length === 0}
              <div class="px-4 py-3 text-xs font-bold text-center opacity-60">No spots found</div>
            {:else}
              {#each spotSuggestions as spot}
                <!-- svelte-ignore a11y-click-events-have-key-events -->
                <!-- svelte-ignore a11y-no-static-element-interactions -->
                <div 
                  class="px-4 py-2.5 hover:bg-[#112D26]/10 cursor-pointer border-b border-[#112D26]/5 last:border-0 transition-colors"
                  on:click={() => selectLocation(spot)}
                >
                  <div class="text-sm font-bold text-[#0F2922] truncate">{spot.name}</div>
                  <div class="text-[10px] font-medium text-[#0F2922]/60 truncate">{spot.region}</div>
                </div>
              {/each}
            {/if}
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Row 1: 3 Columns -->
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
    
    <!-- Box 1: Live Conditions -->
    <div class="bg-[#F8F9F8]/80 backdrop-blur-xl border border-white/60 rounded-[20px] p-5 shadow-sm flex flex-col">
      <h3 class="text-[11px] font-bold uppercase tracking-widest mb-4 truncate">LIVE CONDITIONS - {activeSpot.name}</h3>
      <div class="flex-1 flex flex-col justify-between space-y-3">
        
        <div class="flex items-start gap-4">
          <svg class="w-8 h-8 text-[#0F2922] mt-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 15c3 0 3-4 6-4s3 4 6 4 3-4 6-4" /><path stroke-linecap="round" stroke-linejoin="round" d="M3 20c3 0 3-4 6-4s3 4 6 4 3-4 6-4" /></svg>
          <div>
            <div class="text-[11px] font-bold uppercase text-[#0F2922]/60 tracking-wider">WAVE HEIGHT</div>
            <div class="font-bold text-lg">
              {#if currentWave === "..."}
                <span class="opacity-50">Fetching...</span>
              {:else}
                {currentWave}m ({(parseFloat(currentWave) * 3.28084).toFixed(1)}ft)
              {/if}
            </div>
          </div>
        </div>
        
        <div class="flex items-start gap-4">
          <svg class="w-8 h-8 text-[#0F2922] mt-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>
          <div>
            <div class="text-[11px] font-bold uppercase text-[#0F2922]/60 tracking-wider">WIND</div>
            <div class="font-bold text-lg">
              {#if currentWindSpeed === "..."}
                <span class="opacity-50">Fetching...</span>
              {:else}
                {currentWindSpeed}kt {currentWindDir}
              {/if}
            </div>
          </div>
        </div>
        
        <div class="flex items-start gap-4">
          <svg class="w-8 h-8 text-[#0F2922] mt-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4 14l4-4 4 4 4-4 4 4M4 20l4-4 4 4 4-4 4 4M2 8h20"/></svg>
          <div>
            <div class="text-[11px] font-bold uppercase text-[#0F2922]/60 tracking-wider">TIDE</div>
            <div class="font-bold text-lg">
              {#if highTide.time === "..."}
                <span class="opacity-50">Fetching...</span>
              {:else}
                High {highTide.height}m at {highTide.time}
              {/if}
            </div>
          </div>
        </div>
        
      </div>
    </div>
    
    <!-- Box 2: Swell Forecast -->
    <div class="bg-[#F8F9F8]/80 backdrop-blur-xl border border-white/60 rounded-[20px] overflow-hidden shadow-sm flex flex-col relative h-full min-h-[180px]">
      <div class="p-5 pb-1 flex justify-between items-center z-10">
        <h3 class="text-[11px] font-bold uppercase tracking-widest">SWELL FORECAST</h3>
        <span class="text-[10px] font-medium text-[#0F2922]/60">(5 days)</span>
      </div>
      
      <!-- Vector Art Background -->
      <div class="absolute inset-0 top-12 overflow-hidden pointer-events-none">
        <!-- Sun -->
        <div class="absolute w-24 h-24 bg-[#FF8B6B] rounded-full left-1/2 -translate-x-1/2 top-10 blur-[1px]"></div>
        
        <!-- Wave Layer 1 (Back) -->
        <svg class="absolute bottom-10 w-[120%] -left-[10%] h-32 transition-transform duration-1000" viewBox="0 0 1440 320" preserveAspectRatio="none">
          <path fill="#7DB9C8" fill-opacity="1" d="M0,192L48,170.7C96,149,192,107,288,117.3C384,128,480,192,576,213.3C672,235,768,213,864,186.7C960,160,1056,128,1152,122.7C1248,117,1344,139,1392,150.4L1440,160L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path>
        </svg>
        
        <!-- Wave Layer 2 (Middle) -->
        <svg class="absolute bottom-6 w-[120%] -left-[5%] h-28 transition-transform duration-1000" viewBox="0 0 1440 320" preserveAspectRatio="none">
          <path fill="#4B95B1" fill-opacity="1" d="M0,96L60,117.3C120,139,240,181,360,181.3C480,181,600,139,720,138.7C840,139,960,181,1080,202.7C1200,224,1320,224,1380,224L1440,224L1440,320L1380,320C1320,320,1200,320,1080,320C960,320,840,320,720,320C600,320,480,320,360,320C240,320,120,320,60,320L0,320Z"></path>
        </svg>
        
        <!-- Wave Layer 3 (Front) -->
        <svg class="absolute bottom-0 w-[120%] left-0 h-24 transition-transform duration-1000" viewBox="0 0 1440 320" preserveAspectRatio="none">
          <path fill="#1C7293" fill-opacity="1" d="M0,224L80,213.3C160,203,320,181,480,186.7C640,192,800,224,960,234.7C1120,245,1280,235,1360,229.3L1440,224L1440,320L1360,320C1280,320,1120,320,960,320C800,320,640,320,480,320C320,320,160,320,80,320L0,320Z"></path>
        </svg>
      </div>
      
      <div class="mt-auto relative z-10 w-full pb-4 px-6 pt-10">
        {#if forecastDays.length === 5}
          <div class="flex justify-between text-white font-bold text-sm text-center mb-1 drop-shadow-md">
            {#each forecastDays as day}
               <div class="flex-1">{day.height}m</div>
            {/each}
          </div>
          <div class="flex justify-between text-[10px] font-bold text-[#0F2922] text-center">
            {#each forecastDays as day}
               <div class="flex-1 leading-tight">{@html day.label}</div>
            {/each}
          </div>
        {:else}
          <div class="flex justify-between text-white font-bold text-sm text-center mb-1 drop-shadow-md opacity-50">
            <div class="flex-1">...</div>
          </div>
        {/if}
      </div>
    </div>
    
    <!-- Box 3: Active Alerts -->
    <div class="bg-[#F8F9F8]/80 backdrop-blur-xl border border-white/60 rounded-[20px] p-5 shadow-sm flex flex-col transition-colors duration-500 {(systemAlerts.length + hazards.length) === 0 ? 'bg-[#E9F5E9]/80' : ''}">
      <h3 class="text-[11px] font-bold uppercase tracking-widest mb-4">ACTIVE ALERTS</h3>
      
      <!-- Active Alert Block: system alerts first, then community hazards -->
      {#if (systemAlerts.length + hazards.length) > 0}
        {#each [...systemAlerts, ...hazards].slice(0, 1) as alert}
          <div class="{alert.severity >= 5 ? 'bg-red-600' : alert.severity >= 4 ? 'bg-[#FF8B6B]' : alert.severity >= 3 ? 'bg-amber-500' : 'bg-[#EAB308]'} text-white text-sm font-bold px-4 py-2 rounded-lg inline-flex items-center gap-2 mb-4 w-fit shadow-sm">
            {#if alert.severity >= 5}
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            {:else}
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            {/if}
            {alert.hazard_type}
          </div>
          <p class="text-sm font-medium leading-relaxed mb-3">
            {#if !alert.isSystem}<strong class="text-[#0F2922]/60">Lvl {alert.severity} · {alert.location} › </strong>{/if}
            {alert.description}
          </p>
          {#if (systemAlerts.length + hazards.length) > 1}
            <p class="text-[10px] font-bold uppercase tracking-widest text-[#0F2922]/40 mb-3">+{(systemAlerts.length + hazards.length) - 1} more alert{(systemAlerts.length + hazards.length) > 2 ? 's' : ''} in this area</p>
          {/if}
          {#if !alert.isSystem}
            <button class="text-sm font-bold underline decoration-2 underline-offset-4 hover:text-wave transition-colors w-fit mt-auto" on:click={() => onNavigate('hazard')}>
              Read More
            </button>
          {/if}
        {/each}
      {:else}
        <div class="bg-[#22C55E] text-white text-sm font-bold px-4 py-2 rounded-lg inline-flex items-center gap-2 mb-4 w-fit shadow-sm">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
          All Clear
        </div>
        <p class="text-sm font-medium leading-relaxed mb-4 text-[#0F2922]/70">
          No active hazards currently reported along the coastline. Ocean conditions are safe.
        </p>
      {/if}
    </div>
  </div>

  <!-- Row 2: Surf Timeline -->
  <div class="bg-[#F8F9F8]/80 backdrop-blur-xl border border-white/60 rounded-[20px] p-5 shadow-sm relative overflow-hidden mt-0 mb-0">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-[11px] font-bold uppercase tracking-widest">SURF TIMELINE</h3>
      <div class="text-[10px] font-bold tracking-widest">06:00 - 18:00 ></div>
    </div>
    
    <div class="flex items-center mt-2 relative">
      <span class="text-xs font-bold w-12 flex-shrink-0">TIME</span>
      
      <div class="flex-1 flex justify-between items-center relative z-10 px-4">
        <span class="text-xs font-bold">06:00</span>
        <svg class="w-5 h-5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
        <svg class="w-5 h-5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15c3 0 3-4 6-4s3 4 6 4 3-4 6-4"></path></svg>
        <svg class="w-6 h-6 rounded-full bg-[#112D26] text-white p-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
        <svg class="w-5 h-5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
        <svg class="w-5 h-5 opacity-60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 14l4-4 4 4 4-4 4 4M4 20l4-4 4 4 4-4 4 4M2 8h20"/></svg>
        <svg class="w-5 h-5 opacity-60" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 14l4-4 4 4 4-4 4 4M4 20l4-4 4 4 4-4 4 4M2 8h20"/></svg>
        <svg class="w-5 h-5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
        <svg class="w-5 h-5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
        <svg class="w-5 h-5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
        <svg class="w-5 h-5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
        <span class="text-xs font-bold">18:00</span>
      </div>
    </div>
    
    <!-- Timeline Bar -->
    <div class="flex items-center mt-6 mb-2 relative">
      <span class="text-xs font-bold w-12 flex-shrink-0">SPOTS</span>
      <div class="flex-1 ml-4 h-1 bg-[#0F2922]/10 rounded-full relative">
        <!-- Orange Active Segment -->
        <div class="absolute left-0 top-0 h-full bg-[#FF8B6B] rounded-full w-2/3"></div>
        
        <!-- Dynamic Spot Chips Overlaid -->
        {#each timelineSpots as tspot}
          <!-- svelte-ignore a11y-click-events-have-key-events -->
          <!-- svelte-ignore a11y-no-static-element-interactions -->
          <div class="absolute -top-5 bg-[#F8F9F8] border border-white shadow-md rounded-full px-4 py-1.5 flex items-center gap-4 z-20 cursor-pointer hover:scale-105 transition-all duration-700 ease-out" 
               style="left: {tspot.leftPercent}%"
               on:click={() => {
                  searchQuery = tspot.fullSpot.name;
                  selectLocation(tspot.fullSpot);
               }}>
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
              <div class="leading-tight">
                <div class="text-xs font-bold">{tspot.name}</div>
                <div class="text-[9px] font-medium opacity-70 truncate max-w-[60px]">{tspot.condition}</div>
              </div>
            </div>
            <div class="text-sm font-bold">{tspot.wave}</div>
          </div>
        {/each}
        
        {#if timelineSpots.length === 0}
           <div class="absolute -top-5 left-1/2 -translate-x-1/2 text-xs font-bold opacity-50 bg-[#F8F9F8] px-4 py-1.5 rounded-full border border-white shadow-sm">Calculating peaks...</div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Row 3: Photo Social Feed (with floating Aloha Spirit! overlay) -->
  <div class="relative">
    <!-- Floating Aloha Spirit! sits above the box, partially overlapping the top border -->
    <div class="absolute -top-5 left-1/2 -translate-x-1/2 z-10 pointer-events-none">
      <span class="font-['Caveat'] text-3xl font-bold text-[#112D26] -rotate-2 inline-block drop-shadow-sm">Aloha Spirit!</span>
    </div>
  <div class="bg-[#F8F9F8]/80 backdrop-blur-xl border border-white/60 rounded-[24px] p-5 lg:p-6 shadow-sm">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-[11px] font-bold uppercase tracking-widest">PHOTO SOCIAL FEED</h3>
      <button class="text-[10px] font-bold tracking-widest flex items-center gap-1 hover:opacity-70 transition-opacity" on:click={() => onNavigate('feed')}>
        View Feed <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
      </button>
    </div>
    
    <div class="flex flex-col md:flex-row gap-4 items-center">
      {#each posts as post, i}
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div class="flex-1 w-full relative group cursor-pointer" on:click={() => onNavigate('feed')}>
          <div class="aspect-[4/3] w-full rounded-[16px] overflow-hidden mb-3 shadow-sm border border-black/5 relative">
            {#if post.is_video}
              <!-- svelte-ignore a11y-media-has-caption -->
              <video src={post.first_media} class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"></video>
            {:else}
              <img src={post.first_media} alt="Post" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"/>
            {/if}
            <!-- Profile pic overlay on photo -->
            <div class="absolute top-2 left-2 flex items-center gap-1.5 bg-black/40 backdrop-blur-sm rounded-full px-2 py-1">
              <div class="w-5 h-5 rounded-full bg-[#112D26] flex items-center justify-center text-white text-[8px] font-bold overflow-hidden border border-white/60 flex-shrink-0">
                {#if post.profile_pic_url}
                  <img src={post.profile_pic_url} alt={post.username} class="w-full h-full object-cover"/>
                {:else}
                  {post.username.charAt(0).toUpperCase()}
                {/if}
              </div>
              <span class="text-white text-[9px] font-bold truncate max-w-[55px]">@{post.username}</span>
            </div>
          </div>
          <div class="flex items-center justify-between text-[10px] font-bold">
            <span class="text-[#0F2922]/50 truncate max-w-[80px]">@{post.username}</span>
            <div class="flex items-center gap-1.5 font-medium opacity-80">
              <span class="flex items-center gap-0.5"><svg class="w-2.5 h-2.5 text-[#FF8B6B]" fill="currentColor" stroke="none" viewBox="0 0 24 24"><path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path></svg> {post.likesDisplay}</span>
              <span class="flex items-center gap-0.5"><svg class="w-2.5 h-2.5 text-[#0F2922]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg> {post.commentsDisplay}</span>
            </div>
          </div>
        </div>
      {/each}
      
      <!-- Filler blocks if there are less than 4 posts -->
      {#if posts.length < 4}
        {#each Array(4 - posts.length) as _, i}
          <div class="flex-1 w-full">
            <div class="aspect-[4/3] w-full rounded-[16px] bg-black/5 mb-3 border border-dashed border-black/10"></div>
          </div>
        {/each}
      {/if}
      
      <!-- View More Button -->
      <div class="flex-shrink-0 ml-1 self-end mb-1">
        <button class="bg-[#112D26] text-white text-[10px] font-bold px-4 py-2 rounded-full hover:-translate-y-0.5 transition-transform shadow-md" on:click={() => onNavigate('feed')}>
          View More
        </button>
      </div>
    </div>
  </div>
  </div><!-- /relative wrapper -->
  
</div>
