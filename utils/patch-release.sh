#!/bin/bash

# Script: patch-release.sh
# Description:
#   Cherry-picks a list of commits, amends each with the original commit hash for tracking,
#   and generates a summary from the short github commit messages with links to each commit.
#
# Usage:
#   ./patch-release.sh <commit1> <commit2> ...
#
# Example:
#   ./patch-release.sh abc1234 def5678

set -e

# Check if at least two arguments are provided (repo and at least one commit)
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <commit1> <commit2> ..."
    echo "Example: $0 abc1234 def5678"
    exit 1
fi

GITHUB_REPO="aiidateam/aiida-core"

# Create an array to store commit summaries
declare -a commit_summaries=()

# Loop through each commit hash
for commit in "$@"; do
    # Cherry-pick the commit
    if git cherry-pick "$commit"; then
        # If cherry-pick succeeds, get the short message and short hash
        commit_message=$(git log -1 --pretty=format:"%B" HEAD)
        original_short_hash=$(git log -1 --pretty=format:"%h" "$commit")
        original_long_hash=$(git rev-parse $original_short_hash)

        # Amend the cherry-picked commit to include the original commit ID for tracking
        git commit --amend -m "$commit_message" -m "Cherry-pick: $original_long_hash"

        # Format the output as a Markdown list item and add to the array
        short_commit_message=$(git log -1 --pretty=format:"%s" HEAD)
        cherry_picked_hash=$(git log -1 --pretty=format:"%h" HEAD)
        commit_summaries+=("- $short_commit_message [[${commit}]](https://github.com/$GITHUB_REPO/commit/${original_long_hash})")
    else
        echo "Failed to cherry-pick commit $commit"
        # Abort the cherry-pick in case of conflict
        git cherry-pick --abort
        exit 1
    fi
done

# Print the summary
echo -e "\n### Cherry-Picked Commits Summary:\n"
for summary in "${commit_summaries[@]}"; do
    echo "$summary"
done
