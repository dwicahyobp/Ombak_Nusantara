<script>
  import { fade } from 'svelte/transition';
  
  let searchQuery = '';
  
  const allCams = [
    { name: "Canggu, Bali - Weather Cam", region: "Bali", url: "https://www.youtube.com/embed/L1duJDAqbJY" },
    { name: "Tropical Beach, Bali - Static Cam", region: "Bali", url: "https://www.youtube.com/embed/1avu7zP4dnU" },
    { name: "Crystal Bay Resort", region: "Koh Samui", url: "https://www.youtube.com/embed/Fw9hgttWzIg" },
    { name: "Seychelles Ocean - Static Cam", region: "Seychelles", url: "https://www.youtube.com/embed/Thtj8Ht7Z_c" }
  ];
  
  $: filteredCams = allCams.filter(cam => cam.name.toLowerCase().includes(searchQuery.toLowerCase()) || cam.region.toLowerCase().includes(searchQuery.toLowerCase()));
</script>

<div class="space-y-6">
  <div class="glass-card p-6 flex flex-col md:flex-row justify-between items-center gap-4">
    <div>
      <h3 class="text-2xl font-bold text-accent">Live Surf Cams</h3>
      <p class="text-sm text-textMuted">Check the waves in real-time before you paddle out.</p>
    </div>
    <div class="relative w-full md:w-64 flex-shrink-0">
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg class="w-4 h-4 text-textMuted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
      </div>
      <input 
        type="text" 
        bind:value={searchQuery} 
        placeholder="Search spot or region..." 
        class="input-field !pl-10 !py-2 !text-sm w-full bg-black/40 border-white/5 focus:bg-black/60 focus:border-accent/50"
      >
    </div>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    {#each filteredCams as cam}
      <div transition:fade class="glass-card p-4 flex flex-col gap-3">
        <div class="flex justify-between items-center">
          <h4 class="font-bold text-lg">{cam.name}</h4>
          <span class="text-xs bg-accent/20 text-accent px-2 py-1 rounded-full">{cam.region}</span>
        </div>
        <div class="relative w-full aspect-video bg-black/50 rounded-lg overflow-hidden border border-white/10">
          <iframe 
            src="{cam.url}?autoplay=1&mute=1" 
            title="{cam.name} Live Cam" 
            class="absolute top-0 left-0 w-full h-full" 
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen>
          </iframe>
        </div>
        <div class="text-xs text-textMuted text-right">🔴 LIVE</div>
      </div>
    {/each}
    {#if filteredCams.length === 0}
      <div class="md:col-span-2 text-center py-12 text-textMuted">
        <div class="text-4xl mb-4 opacity-50">🎥</div>
        No live cams found for "{searchQuery}"
      </div>
    {/if}
  </div>
</div>
