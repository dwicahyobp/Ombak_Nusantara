<script>
  import { toasts, removeToast } from '../stores/toast.js';
  import { fly, fade } from 'svelte/transition';
</script>

<div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
  {#each $toasts as toast (toast.id)}
    <div 
      in:fly="{{ y: 20, duration: 300 }}" 
      out:fade 
      class="flex items-center gap-3 px-4 py-3 rounded-lg shadow-xl backdrop-blur-md border 
        {toast.type === 'error' ? 'bg-warning/20 border-warning text-white' : 
         toast.type === 'success' ? 'bg-safe/20 border-safe text-white' : 
         'bg-accent/20 border-accent text-white'}"
    >
      <span>{toast.message}</span>
      <button class="text-white/50 hover:text-white" on:click={() => removeToast(toast.id)}>
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
      </button>
    </div>
  {/each}
</div>
