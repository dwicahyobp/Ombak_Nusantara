<script>
  import { fade, slide, fly } from 'svelte/transition';
  import { tweened } from 'svelte/motion';
  import { cubicOut } from 'svelte/easing';
  import { addToast } from './stores/toast.js';
  import { INDO_SURF_SPOTS } from './surfSpots.js';
  export let user;
  
  let location = '';
  let selectedLat = null;
  let selectedLng = null;
  let region = '';
  let date = '';
  let preferred_time = 'Morning';
  let skill_level = user?.skill_level || 'Beginner';
  
  let result = null;
  let loading = false;
  let pollingInterval = null;
  
  // Parse JSON result for Bento Box
  let parsedResult = null;
  $: {
    if (result) {
      try {
        let cleanResult = result.replace(/```json/g, '').replace(/```/g, '').trim();
        parsedResult = JSON.parse(cleanResult);
      } catch(e) {
        console.error("JSON Parse Error:", e);
        parsedResult = {
           status: "ERROR",
           safety_alert: "Failed to parse AI output. Raw text: " + result,
           live_marine_data: [],
           trip_plan: [],
           local_logistics: [],
           gear_hazards: [],
           hotel_recommendations: []
        };
      }
    } else {
      parsedResult = null;
    }
  }
  
  let spotSuggestions = [];
  let showSuggestions = false;
  let searchTimeout = null;
  
  function handleLocationInput(e) {
    location = e.target.value;
    if (searchTimeout) clearTimeout(searchTimeout);
    
    if (location.trim().length < 2) {
      spotSuggestions = [];
      showSuggestions = false;
      return;
    }
    
    searchTimeout = setTimeout(async () => {
      // 1. Search locally
      const queryLower = location.toLowerCase();
      let localMatches = INDO_SURF_SPOTS.filter(s => 
        s.name.toLowerCase().includes(queryLower) || s.region.toLowerCase().includes(queryLower)
      ).slice(0, 5);
      
      let spots = localMatches.map(s => ({
        name: s.name,
        region: s.region,
        latitude: s.lat,
        longitude: s.lng
      }));
      
      // 2. Search API to fill the rest
      if (spots.length < 5) {
        try {
          const res = await fetch(`https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates?f=json&singleLine=${encodeURIComponent(location)}&sourceCountry=ID&maxLocations=${5 - spots.length}`);
          if (res.ok) {
            const data = await res.json();
            if (data && data.candidates) {
              data.candidates.forEach(r => {
                const parts = r.address.split(',');
                const apiName = parts[0].trim();
                if (!spots.find(s => s.name === apiName)) {
                  spots.push({
                    name: apiName,
                    region: parts.slice(1).join(', ').trim() || 'Indonesia',
                    latitude: r.location.y,
                    longitude: r.location.x
                  });
                }
              });
            }
          }
        } catch (e) {
          console.error("Geocoding error:", e);
        }
      }
      
      spotSuggestions = spots;
      showSuggestions = spotSuggestions.length > 0;
    }, 400);
  }
  
  function selectSpot(spot) {
    location = spot.name;
    region = spot.region;
    selectedLat = spot.latitude;
    selectedLng = spot.longitude;
    spotSuggestions = [];
    showSuggestions = false;
  }
  
  async function generateResearch(overridePrompt = null) {
  if (typeof overridePrompt === 'string') {
    location = overridePrompt;
    selectedLat = null;
    selectedLng = null;
  }
  if (!location || !date || !skill_level) return addToast('Fill all fields', 'warning');
  loading = true;
  result = null;

  try {
    const res = await fetch('/api/surf/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: user.id,
        target_spot: location,
        planned_date: date,
        preferred_time: preferred_time
      })
    });

    if (!res.ok) throw new Error('Failed to generate surf plan');
    const data = await res.json();

    result = data.report_markdown || "No data generated.";
    loading = false;
    addToast('Your Surf Plan is ready!', 'success');
  } catch (e) {
    addToast(e.message, 'error');
    loading = false;
  }
}
  
  function pollResearchJob(jobId) {
    pollingInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/planner/${jobId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.status === 'Completed' || data.status === 'completed') {
            clearInterval(pollingInterval);
            result = data.result_md || data.result_markdown || data.result || "No data generated.";
            loading = false;
            addToast('Your Surf Plan is ready!', 'success');
          } else if (data.status === 'Failed' || data.status === 'failed' || data.status === 'Rejected' || data.status === 'rejected') {
            clearInterval(pollingInterval);
            result = data.result_md || data.error_message || "Research job failed or rejected.";
            loading = false;
            addToast('Research job finished with warning/error.', 'warning');
          }
        }
      } catch (e) {
        clearInterval(pollingInterval);
        loading = false;
      }
    }, 3000);
  }
</script>
<div class="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[70vh]">
  <!-- Left Sidebar (Inputs) -->
  <div class="lg:col-span-3 glass-card-3d space-y-5 h-fit border-t-4 border-t-wave sticky top-6 shadow-glass">
    <div class="inline-flex items-center gap-2 mb-2">
      <span class="w-2 h-2 rounded-full bg-wave animate-pulse"></span>
      <h3 class="text-xs font-bold tracking-widest text-inkSoft uppercase">Research Parameters</h3>
    </div>
    
    <div class="space-y-2 relative">
      <label class="text-xs text-inkSoft uppercase tracking-wider font-bold">Surf Spot / Beach</label>
      <input type="text" value={location} on:input={handleLocationInput} class="input-field bg-white/80" placeholder="e.g. Nias, Mentawai" on:focus={() => {if(spotSuggestions.length) showSuggestions = true;}}>
      {#if showSuggestions}
        <ul class="absolute z-50 w-full bg-surface border border-black/10 rounded-xl mt-1 max-h-48 overflow-y-auto shadow-glass">
          {#each spotSuggestions as spot}
            <li>
              <button class="w-full text-left px-4 py-3 text-sm text-ink hover:bg-surfaceDeep transition-colors" on:click={() => selectSpot(spot)}>
                <span class="block font-semibold">📍 {spot.name}</span>
                <span class="block text-xs text-inkSoft pl-5">{spot.region}</span>
              </button>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
    
    <div class="space-y-2">
      <label class="text-xs text-inkSoft uppercase tracking-wider font-bold">Date</label>
      <input type="date" bind:value={date} class="input-field bg-white/80">
    </div>
    
    <div class="space-y-2">
      <label class="text-xs text-inkSoft uppercase tracking-wider font-bold">Skill Level</label>
      <select bind:value={skill_level} class="input-field bg-white/80">
        <option value="Beginner">Beginner</option>
        <option value="Intermediate">Intermediate</option>
        <option value="Advanced">Advanced</option>
        <option value="Expert">Expert</option>
      </select>
    </div>
    
    <div class="space-y-2">
      <label class="text-xs text-inkSoft uppercase tracking-wider font-bold">Preferred Time</label>
      <select bind:value={preferred_time} class="input-field bg-white/80 text-sm">
        <option value="Morning">Morning (6am - 10am)</option>
        <option value="Midday">Midday (10am - 2pm)</option>
        <option value="Afternoon">Afternoon (2pm - 6pm)</option>
      </select>
    </div>
    
    <button class="btn-primary w-full mt-6 bg-wave text-white font-bold shadow-md hover:shadow-lg" on:click={generateResearch} disabled={loading}>
      {#if loading}
        <div class="flex items-center justify-center gap-2">
          <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          Crafting Itinerary...
        </div>
      {:else}
        Craft My Surf Session
      {/if}
    </button>
  </div>
  
  <!-- Right Output Area -->
  <div class="lg:col-span-9 space-y-6">
    {#if loading}
      <div class="glass-card h-full flex flex-col items-center justify-center text-center gap-6 min-h-[500px] shadow-glass border-white/50">
        <div class="relative w-32 h-32">
          <div class="absolute inset-0 border-t-4 border-wave rounded-full animate-spin"></div>
          <div class="absolute inset-4 border-r-4 border-coral rounded-full animate-spin" style="animation-direction: reverse; animation-duration: 1.5s;"></div>
          <div class="absolute inset-8 border-b-4 border-deep rounded-full animate-spin" style="animation-duration: 2s;"></div>
          <div class="absolute inset-12 bg-wave/20 rounded-full animate-pulse"></div>
        </div>
        <div class="space-y-2">
          <h3 class="text-3xl font-display font-bold text-gradient-wave">Deep Diving...</h3>
          <p class="text-sm text-inkSoft max-w-md mx-auto">Our Surf Engine is scouring local Indonesian databases, historical oceanographic records, and coastal community forums.</p>
        </div>
      </div>
    {:else if result}
      <!-- Bento Grid Layout for AI Surf Plan (JSON) -->
      {#if parsedResult}
      <div in:fly={{y: 20, duration: 600, delay: 200}} class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

  <!-- Status Box (Full Width) -->
  <div class="col-span-1 md:col-span-2 lg:col-span-3 glass-card-3d relative overflow-hidden p-6 md:p-8 {parsedResult.status === 'REJECTED' ? 'bg-red-500/10 border-red-500/50' : 'bg-safe/10 border-safe/50'}">
    <div class="flex items-center gap-4 mb-3">
      <span class="text-4xl animate-pulse">{parsedResult.status === 'REJECTED' ? '🛑' : '✅'}</span>
      <h3 class="text-2xl font-bold font-display {parsedResult.status === 'REJECTED' ? 'text-red-500' : 'text-safe'}">Status: {parsedResult.status}</h3>
    </div>
  </div>

  <!-- Surf Conditions Box -->
  <div class="glass-card-3d bg-white/40 p-6 border border-white/80 group hover:border-wave/50">
    <h3 class="text-sm font-bold tracking-widest text-wave uppercase mb-4 pb-2 border-b border-black/5">📊 Surf Conditions</h3>
    <div class="prose prose-sm max-w-none text-ink">
      {@html window.marked ? window.marked.parse(parsedResult.surf_conditions || '') : parsedResult.surf_conditions}
    </div>
  </div>

  <!-- Gear & Hazards Box -->
  <div class="glass-card-3d bg-white/40 p-6 border border-white/80 group hover:border-wave/50">
    <h3 class="text-sm font-bold tracking-widest text-coral uppercase mb-4 pb-2 border-b border-black/5">🎒 Gear & Hazards</h3>
    <div class="prose prose-sm max-w-none text-ink">
      {@html window.marked ? window.marked.parse(parsedResult.gear_hazards || '') : parsedResult.gear_hazards}
    </div>
  </div>

  <!-- Where to Stay Box -->
  <div class="glass-card-3d bg-white/40 p-6 border border-white/80 group hover:border-wave/50">
    <h3 class="text-sm font-bold tracking-widest text-wave uppercase mb-4 pb-2 border-b border-black/5">🏨 Where to Stay</h3>
    <div class="prose prose-sm max-w-none text-ink">
      {@html window.marked ? window.marked.parse(parsedResult.hotel_recommendations || '') : parsedResult.hotel_recommendations}
    </div>
  </div>

  <!-- Local Logistics Box -->
  <div class="glass-card-3d bg-white/40 p-6 border border-white/80 group hover:border-wave/50">
    <h3 class="text-sm font-bold tracking-widest text-wave uppercase mb-4 pb-2 border-b border-black/5">💼 Logistics</h3>
    <div class="prose prose-sm max-w-none text-ink">
      {@html window.marked ? window.marked.parse(parsedResult.local_ecosystem || '') : parsedResult.local_ecosystem}
    </div>
  </div>

  <!-- Comprehensive Itinerary Box (Spans 2 columns on lg) -->
  <div class="md:col-span-1 lg:col-span-2 glass-card-3d bg-white/40 p-6 border border-white/80 group hover:border-wave/50">
    <h3 class="text-sm font-bold tracking-widest text-wave uppercase mb-4 pb-2 border-b border-black/5">📅 Timeline Itinerary</h3>
    <div class="prose prose-sm max-w-none text-ink">
      {@html window.marked ? window.marked.parse(parsedResult.trip_plan || '') : parsedResult.trip_plan}
    </div>
  </div>

</div>
      {/if}
    {:else}
      <div class="glass-card h-full flex flex-col items-center justify-center text-center gap-6 border-dashed border-2 border-wave/20 bg-white/30 backdrop-blur-sm min-h-[500px]">
        <div class="mb-6 animate-bounce text-wave opacity-80 hover-float cursor-default">
          <svg class="w-24 h-24 drop-shadow-sm" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"></path>
          </svg>
        </div>
        <h3 class="text-4xl font-display font-bold text-gradient-wave">Ready for Your Next Swell</h3>
        <p class="text-lg max-w-lg text-inkSoft font-medium leading-relaxed">Enter the target surf spot, date, and your skill level in the panel on the left to initiate an expansive intelligence sweep and generate your itinerary.</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background-color: rgba(0,0,0,0.1);
    border-radius: 20px;
  }
  /* Enhancements for Bento Box Markdown */
  :global(.glass-card-3d p) {
    margin-bottom: 0 !important;
  }
</style>
