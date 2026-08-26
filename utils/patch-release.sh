#!/bin/bash

# Script: patch-release.sh
# Description:
#   Cherry-picks a list of commits, amends each with the original commit hash for tracking,
#   and generates a summary from the short github commit messages with links to each commit.
#
# Usage:
#   ./patch-release.sh [--dry-run] <commit1> <commit2> ...
#
# Example:
#   ./patch-release.sh abc1234 def5678
#   ./patch-release.sh --dry-run abc1234 def5678

set -e

GITHUB_REPO="aiidateam/aiida-core"
DRY_RUN=false

# Cleanup function in case of interruption
cleanup() {
    if git cherry-pick --abort 2>/dev/null; then
        echo "⚠️  Cleaned up incomplete cherry-pick"
    fi
}
trap cleanup EXIT

# Parse options
if [ "$1" = "--dry-run" ]; then
    DRY_RUN=true
    shift
fi

# Check if at least one commit is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 [--dry-run] <commit1> <commit2> ..."
    echo "Example: $0 abc1234 def5678"
    exit 1
fi

# Safety check: prevent running on main branch
current_branch=$(git branch --show-current)
if [ "$current_branch" = "main" ]; then
    echo "❌ Error: Cannot run patch-release on main branch"
    echo "Please checkout a release branch first (e.g., git checkout -b release-2.7.2)"
    exit 1
fi

# Verify all commits exist
echo "Verifying commits..."
for commit in "$@"; do
    if ! git rev-parse --verify "$commit" >/dev/null 2>&1; then
        echo "❌ Error: Commit '$commit' not found"
        exit 1
    fi
done

# Show what will be done
echo ""
echo "Branch: $current_branch"
echo "About to cherry-pick ${#@} commits:"
echo ""
for commit in "$@"; do
    git log -1 --oneline "$commit"
done
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "🔍 DRY RUN MODE - No changes will be made"
    echo ""
else
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    echo ""
fi

# Create an array to store commit summaries
declare -a commit_summaries=()
total=$#
current=0

# Loop through each commit hash
for commit in "$@"; do
    ((current++))

    # Get commit info upfront
    original_short_hash=$(git rev-parse --short "$commit")
    original_long_hash=$(git rev-parse "$commit")
    commit_message=$(git log -1 --pretty=format:"%B" "$commit")
    short_commit_message=$(git log -1 --pretty=format:"%s" "$commit")

    echo "[$current/$total] Cherry-picking $original_short_hash: $short_commit_message"

    if [ "$DRY_RUN" = true ]; then
        # Dry run: just show what would happen
        pr_number=$(echo "$commit_message" | grep -oP '#\K\d+' || echo "")
        if [ -n "$pr_number" ]; then
            commit_summaries+=("- $short_commit_message [[#${pr_number}]](https://github.com/$GITHUB_REPO/pull/${pr_number})")
        else
            commit_summaries+=("- $short_commit_message [[${original_short_hash}]](https://github.com/$GITHUB_REPO/commit/${original_long_hash})")
        fi
    else
        # Actually cherry-pick
        if git cherry-pick "$commit"; then
            # If cherry-pick succeeds, amend with tracking info
            git commit --amend -m "$commit_message" -m "Cherry-pick: $original_long_hash"

            # Extract PR number if present
            pr_number=$(echo "$commit_message" | grep -oP '#\K\d+' || echo "")
            if [ -n "$pr_number" ]; then
                commit_summaries+=("- $short_commit_message [[#${pr_number}]](https://github.com/$GITHUB_REPO/pull/${pr_number})")
            else
                commit_summaries+=("- $short_commit_message [[${original_short_hash}]](https://github.com/$GITHUB_REPO/commit/${original_long_hash})")
            fi

            echo "  ✅ Success"
        else
            echo "  ❌ Failed to cherry-pick commit $commit"
            echo ""
            echo "Conflict detected. You can:"
            echo "  1. Resolve conflicts manually, then run: git cherry-pick --continue"
            echo "  2. Skip this commit with: git cherry-pick --skip"
            echo "  3. Abort the entire process with: git cherry-pick --abort"
            echo ""
            exit 1
        fi
    fi
done

# Print the summary
echo ""
echo "=========================================="
if [ "$DRY_RUN" = true ]; then
    echo "### Cherry-Pick Preview (Dry Run):"
else
    echo "### Cherry-Picked Commits Summary:"
fi
echo ""
for summary in "${commit_summaries[@]}"; do
    echo "$summary"
done
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "ℹ️  This was a dry run. Run without --dry-run to actually cherry-pick."
else
    echo "✅ All commits cherry-picked successfully!"
    echo "📋 Copy the summary above for your release notes."
fi
