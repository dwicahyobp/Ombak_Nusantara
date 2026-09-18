<script>
  import { onMount, tick } from 'svelte';
  import { fade, slide } from 'svelte/transition';
  import { INDO_SURF_SPOTS } from './surfSpots.js';
  
  let map;
  let activeSpot = null;
  let chart = null;
  let loadingData = false;
  let searchQuery = '';
  let showSuggestions = false;
  
  let searchTimeout = null;
  let filteredSpots = [];
  
  function handleLocationInput(e) {
    searchQuery = e.target.value;
    if (searchTimeout) clearTimeout(searchTimeout);
    
    if (searchQuery.trim().length < 2) {
      filteredSpots = [];
      showSuggestions = false;
      return;
    }
    
    searchTimeout = setTimeout(async () => {
      // 1. Search locally in Curated Database
      const queryLower = searchQuery.toLowerCase();
      let localMatches = INDO_SURF_SPOTS.filter(s => 
        s.name.toLowerCase().includes(queryLower) || s.region.toLowerCase().includes(queryLower)
      ).slice(0, 5);
      
      let spots = localMatches.map(s => ({
        name: s.name,
        region: s.region,
        lat: s.lat,
        lng: s.lng
      }));

      // 2. Search API to fill the rest up to 5
      if (spots.length < 5) {
        try {
          const res = await fetch(`https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?f=json&singleLine=${encodeURIComponent(searchQuery)}&sourceCountry=ID&maxLocations=${5 - spots.length}`);
          if (res.ok) {
            const data = await res.json();
            if (data && data.candidates) {
              data.candidates.forEach(r => {
                const parts = r.address.split(',');
                const apiName = parts[0].trim();
                // Avoid duplicates by name
                if (!spots.find(s => s.name === apiName)) {
                  spots.push({
                    name: apiName,
                    region: parts.slice(1).join(', ').trim() || 'Indonesia',
                    lat: r.location.y,
                    lng: r.location.x
                  });
                }
              });
            }
          }
        } catch (e) {
          console.error("Geocoding error:", e);
        }
      }
      
      filteredSpots = spots;
      showSuggestions = filteredSpots.length > 0;
    }, 400);
  }

  onMount(() => {
    // Initialize map
    map = L.map('surfMap', {
      zoomControl: false
    }).setView([-4.0, 115.0], 5); // Center on Indonesia
    
    L.control.zoom({ position: 'bottomleft' }).addTo(map);

    // Add CartoDB Voyager (Bright, clean, Google Maps style)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; CartoDB',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(map);

    // Custom Glowing Pulse Icon (Blue/Cyan for bright map)
    const surfIcon = L.divIcon({
      className: 'custom-div-icon',
      html: `
        <div class="relative flex items-center justify-center w-12 h-12 hover:scale-125 transition-transform duration-300 cursor-pointer">
          <span class="absolute inline-flex w-10 h-10 rounded-full bg-accent opacity-40 animate-ping"></span>
          <div class="relative flex items-center justify-center w-10 h-10 bg-gradient-to-br from-[#00B4D8] to-[#0077B6] rounded-full shadow-[0_0_20px_#00B4D8] border-2 border-white/80">
            <span class="text-xl ml-1">🏄‍♂️</span>
          </div>
        </div>
      `,
      iconSize: [48, 48],
      iconAnchor: [24, 24]
    });

    // We don't add any default markers! Clean map!
  });

  function handleSpotSelect(spot) {
    searchQuery = '';
    showSuggestions = false;
    
    // Remove old markers
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker) {
        map.removeLayer(layer);
      }
    });

    // Create custom icon
    const surfIcon = L.divIcon({
      className: 'custom-div-icon',
      html: `
        <div class="relative flex items-center justify-center w-12 h-12 hover:scale-125 transition-transform duration-300 cursor-pointer">
          <span class="absolute inline-flex w-10 h-10 rounded-full bg-accent opacity-40 animate-ping"></span>
          <div class="relative flex items-center justify-center w-10 h-10 bg-gradient-to-br from-[#00B4D8] to-[#0077B6] rounded-full shadow-[0_0_20px_#00B4D8] border-2 border-white/80">
            <span class="text-xl ml-1">🏄‍♂️</span>
          </div>
        </div>
      `,
      iconSize: [48, 48],
      iconAnchor: [24, 24]
    });

    // Add new marker
    const marker = L.marker([spot.lat, spot.lng], { icon: surfIcon }).addTo(map);
    marker.bindTooltip(`<b>${spot.name}</b>`, { direction: 'top', offset: [0, -15], className: 'glass-tooltip' }).openTooltip();
    marker.on('click', () => {
      map.flyTo([spot.lat, spot.lng + 0.2], 11, { duration: 1.5 });
      openSpotPanel(spot);
    });
    
    // Cinematic Zoom: Fly close to the beach.
    // By adding +0.2 to longitude, the map's center is shifted to the East, forcing the marker to appear on the Left side of the screen!
    map.flyTo([spot.lat, spot.lng + 0.2], 11, { duration: 2, easeLinearity: 0.25 });
    
    openSpotPanel(spot);
  }

  async function openSpotPanel(spot) {
    activeSpot = spot;
    loadingData = true;
    
    try {
      // Fetch marine data directly from Open-Meteo
      const res = await fetch(`https://marine-api.open-meteo.com/v1/marine?latitude=${spot.lat}&longitude=${spot.lng}&hourly=wave_height,wave_period,wave_direction&timezone=auto`);
      const data = await res.json();
      
      const resWind = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${spot.lat}&longitude=${spot.lng}&hourly=wind_speed_10m,temperature_2m,uv_index&timezone=auto`);
      const dataWind = await resWind.json();
      
      // Generate Mock Tide Data (since Open-Meteo Marine API doesn't provide tides globally)
      const tideHeights = [];
      const now = new Date();
      for (let i = 0; i < 48; i++) {
        // Semi-diurnal tide (period ~ 12.4 hours)
        const tide = 1.5 + Math.sin(((now.getHours() + i) / 12.4) * Math.PI * 2) * 1.2;
        tideHeights.push(tide);
      }
      
      loadingData = false;
      await tick(); 
      
      renderChart(data.hourly, dataWind.hourly, tideHeights);
    } catch (e) {
      console.error(e);
      loadingData = false;
    }
  }

  function renderChart(marineData, windData, tideHeights) {
    if (chart) chart.destroy();
    
    // Take next 48 hours
    const labels = marineData.time.slice(0, 48).map(t => new Date(t).toLocaleTimeString([], {hour: '2-digit'}));
    const waveHeights = marineData.wave_height.slice(0, 48);
    const windSpeeds = windData.wind_speed_10m.slice(0, 48);
    const temps = windData.temperature_2m.slice(0, 48);
    
    activeSpot.currentTemp = temps[0];
    activeSpot.currentWave = waveHeights[0];
    activeSpot.currentWind = windSpeeds[0];
    activeSpot.maxTide = Math.max(...tideHeights.slice(0, 24)).toFixed(1);

    const ctx = document.getElementById('forecastChart').getContext('2d');
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Wave Height (m)',
            data: waveHeights,
            borderColor: '#00B4D8',
            backgroundColor: 'rgba(0, 180, 216, 0.1)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            yAxisID: 'y'
          },
          {
            label: 'Tide Curve (m)',
            data: tideHeights,
            borderColor: '#F28F3B',
            borderWidth: 2,
            tension: 0.4,
            yAxisID: 'y'
          },
          {
            label: 'Wind Speed (km/h)',
            data: windSpeeds,
            borderColor: '#E2E8F0',
            borderDash: [5, 5],
            borderWidth: 2,
            tension: 0.4,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: '#56727C' } }
        },
        scales: {
          x: { ticks: { color: '#56727C', maxTicksLimit: 8 }, grid: { color: 'rgba(0,0,0,0.05)' } },
          y: { type: 'linear', display: true, position: 'left', title: { display: true, text: 'Meters (Wave & Tide)', color: '#00B4D8' }, ticks: { color: '#00B4D8' }, grid: { color: 'rgba(0,0,0,0.05)' } },
          y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: 'Wind (km/h)', color: '#93AAB0' }, ticks: { color: '#93AAB0' }, grid: { drawOnChartArea: false } }
        }
      }
    });
  }
</script>

<style>
  :global(.glass-tooltip) {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(0,0,0,0.1) !important;
    color: #0E2A33 !important;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }
  :global(.glass-tooltip::before) {
    display: none;
  }
</style>

<div class="relative w-full h-[calc(100vh-16rem)] min-h-[600px] border-4 border-white/50 shadow-[0_8px_32px_0_rgba(31,38,135,0.15)] overflow-hidden rounded-3xl animate-fade-up">
  <!-- The Map Container (Always 100% Size) -->
  <div id="surfMap" class="absolute inset-0 w-full h-full bg-surface"></div>

  <!-- Floating Predictive Search Bar (Top Left) -->
  <div class="absolute top-6 left-6 w-[400px] max-w-[90%] z-[2000]">
    <div class="relative">
      <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none z-10">
        <svg class="w-6 h-6 text-inkSoft drop-shadow-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
      </div>
      <input 
        type="text" 
        value={searchQuery}
        on:input={handleLocationInput}
        on:focus={() => {if(filteredSpots.length) showSuggestions = true;}}
        placeholder="Find your beach... (e.g. Uluwatu, Nias)"
        class="w-full pl-12 pr-4 py-4 bg-white/80 backdrop-blur-xl border-2 border-white/80 rounded-2xl text-ink placeholder-inkSoft font-bold focus:outline-none focus:ring-4 focus:ring-wave/30 shadow-[0_8px_32px_0_rgba(31,38,135,0.1)] transition-all hover-float"
      >
      
      {#if showSuggestions && searchQuery.length > 0}
        <div class="absolute top-full mt-2 w-full bg-white/95 backdrop-blur-xl border border-black/10 rounded-2xl overflow-hidden shadow-glass">
          {#each filteredSpots as spot}
            <button 
              class="w-full text-left px-6 py-4 border-b border-black/5 hover:bg-surface transition-colors flex justify-between items-center group"
              on:click={() => handleSpotSelect(spot)}
            >
              <div>
                <div class="font-bold text-ink group-hover:text-wave transition-colors">{spot.name}</div>
                <div class="text-sm text-inkSoft">{spot.region}</div>
              </div>
              <div class="text-wave opacity-0 group-hover:opacity-100 transition-opacity">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
              </div>
            </button>
          {/each}
          {#if filteredSpots.length === 0}
            <div class="px-6 py-4 text-inkSoft text-center">Spot tidak ditemukan</div>
          {/if}
        </div>
      {/if}
    </div>
  </div>

  <!-- Giant Glassmorphism Dashboard Panel Overlay -->
  {#if activeSpot}
    <div transition:slide={{ axis: 'x', duration: 500 }} class="absolute right-0 top-0 bottom-0 w-full md:w-[600px] h-full bg-white/70 backdrop-blur-2xl border-l border-white/80 rounded-l-3xl p-8 flex flex-col z-[1000] overflow-y-auto shadow-[-10px_0_30px_rgba(0,0,0,0.1)]">
      <div class="flex justify-between items-start mb-8">
        <div>
          <h3 class="text-5xl font-display font-black text-gradient-wave mb-2">{activeSpot.name}</h3>
          <p class="text-xl text-inkSoft font-script tracking-wide">📍 {activeSpot.region}</p>
        </div>
        <button class="p-2 bg-black/5 hover:bg-black/10 rounded-full text-inkSoft transition-colors" on:click={() => {activeSpot = null; map.flyTo([-4.0, 115.0], 5, {duration: 1})}}>
          <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
      
      {#if loadingData}
        <div class="flex-1 flex flex-col items-center justify-center space-y-6">
          <div class="w-16 h-16 border-4 border-wave border-t-transparent rounded-full animate-spin drop-shadow-sm"></div>
          <p class="text-lg text-inkSoft animate-pulse font-medium">Syncing Satellite Telemetry...</p>
        </div>
      {:else}
        <!-- Core Stats Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div class="glass-card-3d bg-white/60 p-4 text-center border border-white flex flex-col justify-center">
            <div class="text-3xl font-display font-black text-wave mb-1">{activeSpot.currentWave}m</div>
            <div class="text-[10px] text-inkSoft uppercase tracking-widest font-bold">Wave Height</div>
          </div>
          <div class="glass-card-3d bg-white/60 p-4 text-center border border-white flex flex-col justify-center">
            <div class="text-3xl font-display font-black text-ink mb-1">{activeSpot.currentWind}</div>
            <div class="text-[10px] text-inkSoft uppercase tracking-widest font-bold">km/h Wind</div>
          </div>
          <div class="glass-card-3d bg-white/60 p-4 text-center border border-white flex flex-col justify-center">
            <div class="text-3xl font-display font-black text-coral mb-1">{activeSpot.currentTemp}°</div>
            <div class="text-[10px] text-inkSoft uppercase tracking-widest font-bold">Temperature</div>
          </div>
          <div class="glass-card-3d bg-white/60 p-4 text-center border border-white flex flex-col justify-center">
            <div class="text-3xl font-display font-black text-[#F28F3B] mb-1">{activeSpot.maxTide}m</div>
            <div class="text-[10px] text-inkSoft uppercase tracking-widest font-bold">Max Tide</div>
          </div>
        </div>
        
        <!-- Giant Chart Area -->
        <div class="flex-1 flex flex-col glass-card-3d bg-white/60 p-6 border border-white">
          <h4 class="text-xl font-bold mb-6 flex items-center gap-3 font-display"><span class="text-wave text-3xl hover-float">📈</span> 48-Hour Wave & Wind Forecast</h4>
          <div class="relative flex-1 w-full min-h-[350px]">
            <canvas id="forecastChart"></canvas>
          </div>
        </div>
        
        <!-- Source Data Attribution -->
        <div class="text-[10px] text-inkSoft italic text-right mt-4 pt-4 border-t border-black/5">
          Weather & Marine Data powered by <a href="https://open-meteo.com/" target="_blank" class="hover:text-ink transition-colors font-semibold">Open-Meteo API</a>
        </div>
      {/if}
    </div>
  {/if}
</div>
