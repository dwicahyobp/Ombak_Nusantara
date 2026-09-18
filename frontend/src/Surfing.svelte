<script>
  import SurfPlanner from './SurfPlanner.svelte';
  import MyHistory from './MyHistory.svelte';
  import SurfMap from './SurfMap.svelte';

  export let user;
  export let isGuest = false;

  // If user is guest, force 'research', else default to 'map'
  let subTab = isGuest ? 'research' : 'map';
</script>

<div class="space-y-6 relative">
  <!-- Background Encouragement Text -->
  <div class="absolute right-[2%] md:right-[5%] -top-10 md:-top-14 font-script text-2xl md:text-3xl font-bold -rotate-2 text-wave/40 opacity-70 pointer-events-none select-none z-10 max-w-lg text-right leading-tight">
    "Catch the waves and let the sea set you free."
  </div>
  <!-- Sub-navigation -->
  <div class="flex gap-4 border-b border-black/5 pb-4 overflow-x-auto">
    <button 
      class="px-6 py-2 whitespace-nowrap rounded-full font-semibold transition-all {subTab === 'map' ? 'bg-wave text-white shadow-md' : 'bg-surface text-inkSoft hover:bg-surfaceDeep hover:text-ink shadow-sm'}"
      on:click={() => subTab = 'map'}
    >
      🗺️ Surf Map
    </button>
    <button 
      class="px-6 py-2 whitespace-nowrap rounded-full font-semibold transition-all {subTab === 'research' ? 'bg-wave text-white shadow-md' : 'bg-surface text-inkSoft hover:bg-surfaceDeep hover:text-ink shadow-sm'}"
      on:click={() => subTab = 'research'}
    >
      🏄 Surf Plan
    </button>
  </div>
  
  <!-- Content -->
  <div class="pt-2">
    {#if subTab === 'map'}
      <div class="w-full">
        <SurfMap />
      </div>
    {:else if subTab === 'research'}
      <div class="space-y-12">
        <SurfPlanner {user} />
        
        {#if !isGuest}
          <!-- History Section -->
          <div class="border-t border-black/5 pt-8">
            <h3 class="text-2xl font-bold mb-6 text-ink">📖 My Surf Plans</h3>
            <MyHistory {user} />
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>
