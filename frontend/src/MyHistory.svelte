<script>
  import { onMount } from 'svelte';
  import { slide } from 'svelte/transition';
  import { addToast } from './stores/toast.js';
  export let user;
  
  let history = [];
  let expandedItems = {};
  
  function toggleExpand(id) {
    expandedItems[id] = !expandedItems[id];
  }
  
  function parseJSONResult(str) {
    if (!str) return null;
    try {
      return JSON.parse(str);
    } catch (e) {
      return null;
    }
  }
  
  async function loadHistory() {
    try {
      const res = await fetch(`/api/surf/users/${user.id}/plans`);
      if (res.ok) {
        const data = await res.json();
        history = data.plans || [];
      }
    } catch (e) {
      console.error(e);
    }
  }
  
  async function deletePlan(planId) {
    if (!confirm('Are you sure you want to delete this surf plan?')) return;
    
    try {
      const res = await fetch(`/api/surf/plans/${planId}?user_id=${user.id}`, {
        method: 'DELETE'
      });
      
      if (!res.ok) throw new Error('Failed to delete plan');
      
      history = history.filter(item => item.plan_id !== planId);
      addToast('Surf plan deleted successfully', 'success');
    } catch (e) {
      addToast(e.message, 'error');
    }
  }

  onMount(loadHistory);
</script>

<div class="space-y-4">
  {#if history.length === 0}
    <div class="glass-card text-center py-16 flex flex-col items-center justify-center gap-4">
      <div class="text-6xl opacity-50">🏄‍♂️</div>
      <h3 class="text-xl font-bold text-ink">No Surf Plans Yet</h3>
      <p class="text-inkSoft max-w-sm mx-auto">You haven't generated any surf plans. Head over to the Surf Planning tab to get AI-powered conditions and safety reports!</p>
    </div>
  {:else}
    {#each history as item}
      <div class="glass-card border-l-4 border-l-wave !p-0 overflow-hidden relative shadow-sm">
        <button 
          class="absolute top-4 right-4 text-inkSoft hover:text-warning transition-colors z-10"
          on:click={() => deletePlan(item.plan_id)}
          title="Delete Plan"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
        </button>

        <div 
          class="w-full flex justify-between items-center p-4 hover:bg-surfaceDeep transition-colors cursor-pointer text-left pr-12"
          on:click={() => toggleExpand(item.plan_id)}
          on:keydown={(e) => e.key === 'Enter' && toggleExpand(item.plan_id)}
          role="button"
          tabindex="0"
        >
          <div>
            <h4 class="text-lg font-bold text-ink">📍 {item.target_spot}</h4>
            <p class="text-sm text-inkSoft">📅 {item.planned_date} • <span class="text-wave">{item.status}</span></p>
          </div>
          <div class="text-inkSoft">
            {#if expandedItems[item.plan_id]}
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path></svg>
            {:else}
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
            {/if}
          </div>
        </div>
        
        {#if expandedItems[item.plan_id]}
          <div transition:slide={{ duration: 300 }} class="p-4 pt-0 border-t border-black/5 mt-2">
            {#if item.report && item.report.content_md}
              {@const parsedResult = parseJSONResult(item.report.content_md)}
              
              {#if parsedResult && parsedResult.surf_conditions}
                <!-- Bento Box Layout -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <!-- Box 1: Surf Conditions (Overview) -->
                  <div class="glass-card relative overflow-hidden bg-white border border-black/5 hover:border-wave/40 shadow-sm transition-colors h-full p-6 group">
                    <div class="absolute inset-0 bg-gradient-to-br from-wave/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
                    <div class="prose prose-premium max-w-none prose-sm prose-headings:text-center prose-headings:text-wave mb-4">
                      {@html window.marked ? window.marked.parse(parsedResult.surf_conditions) : parsedResult.surf_conditions}
                    </div>
                    <div class="pt-2 border-t border-black/5 text-[10px] text-inkSoft italic text-right mt-auto relative z-10">
                      Real-time data powered by Open-Meteo & AI
                    </div>
                  </div>
                  
                  <!-- Box 2: Gear & Hazards -->
                  {#if parsedResult.gear_hazards}
                    <div class="glass-card relative overflow-hidden bg-white border border-black/5 hover:border-wave/40 shadow-sm transition-colors h-full p-6 group">
                      <div class="absolute inset-0 bg-gradient-to-br from-wave/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
                      <div class="prose prose-premium max-w-none prose-sm prose-headings:text-center prose-headings:text-wave">
                        {@html window.marked ? window.marked.parse(parsedResult.gear_hazards) : parsedResult.gear_hazards}
                      </div>
                    </div>
                  {/if}

                  <!-- Box 3: Hotel / Accommodation -->
                  {#if parsedResult.hotel_recommendations}
                    <div class="glass-card relative overflow-hidden bg-white border border-black/5 hover:border-wave/40 shadow-sm transition-colors h-full p-6 group">
                      <div class="absolute inset-0 bg-gradient-to-br from-wave/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
                      <div class="prose prose-premium max-w-none prose-sm prose-headings:text-center prose-headings:text-wave">
                        {@html window.marked ? window.marked.parse(parsedResult.hotel_recommendations) : parsedResult.hotel_recommendations}
                      </div>
                    </div>
                  {/if}
                  
                  <!-- Box 4: Local Ecosystem (Logistics) -->
                  <div class="glass-card relative overflow-hidden bg-white border border-black/5 hover:border-wave/40 shadow-sm transition-colors h-full p-6 group">
                    <div class="absolute inset-0 bg-gradient-to-br from-wave/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
                    <div class="prose prose-premium max-w-none prose-sm prose-headings:text-center prose-headings:text-wave">
                      {@html window.marked ? window.marked.parse(parsedResult.local_ecosystem) : parsedResult.local_ecosystem}
                    </div>
                  </div>
                  
                  <!-- Box 5: Trip Plan (Itinerary) - Full Width Bottom -->
                  <div class="glass-card relative overflow-hidden bg-white border border-black/5 hover:border-wave/40 shadow-sm transition-colors h-full p-6 group md:col-span-2 mt-4">
                    <div class="absolute inset-0 bg-gradient-to-br from-wave/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>
                    <div class="prose prose-premium max-w-none prose-sm prose-headings:text-center prose-headings:text-wave">
                      {@html window.marked ? window.marked.parse(parsedResult.trip_plan) : parsedResult.trip_plan}
                    </div>
                  </div>
                </div>
              {:else}
                <!-- Legacy Layout -->
                <div class="bg-surfaceDeep p-4 rounded-lg prose max-w-none text-sm mt-4">
                  {@html window.marked ? window.marked.parse(item.report.content_md) : item.report.content_md}
                </div>
              {/if}
            {:else}
              <p class="text-warning mt-4">Report not available</p>
            {/if}
          </div>
        {/if}
      </div>
    {/each}
  {/if}
</div>

<style>
  /* Enhance the Markdown Headings to look like Premium Card Headers */
  :global(.prose h3) {
    text-align: center !important;
    border-bottom: 1px solid rgba(0, 0, 0, 0.1) !important;
    padding-bottom: 0.75rem !important;
    margin-top: 0 !important;
    margin-bottom: 1rem !important;
    display: block !important;
    width: 100% !important;
  }
  
  /* Add generous spacing after lists to separate Sub-Headlines */
  :global(.prose ul) {
    margin-bottom: 1.75rem !important;
  }
  
  /* Keep the Sub-Headline (strong tag inside p) close to its list */
  :global(.prose p) {
    margin-bottom: 0.5rem !important;
    margin-top: 0 !important;
  }
  
  /* Add spacing between bullet points for better readability */
  :global(.prose li) {
    margin-bottom: 0.5rem !important;
  }
</style>
