<?php
/**
 * Plugin Name: AgentNexus Agent-Native
 * Description: Makes WordPress agent-friendly (llms.txt, headers, api-catalog stub)
 * Version: 0.1
 */

add_action('init', function() {
    // Stub: Add headers
    header('X-Agent-Native: v0.1');
});

// Future: Generate llms.txt on /llms.txt
add_action('template_redirect', function() {
    if (isset($_GET['llms'])) {
        header('Content-Type: text/markdown');
        echo "# LLMs.txt stub from AgentNexus WordPress plugin\n";
        exit;
    }
});
